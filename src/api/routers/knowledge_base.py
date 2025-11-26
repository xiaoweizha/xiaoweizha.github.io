"""
知识库管理API路由

提供知识库的创建、管理、查询等功能。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
import asyncio
import json

from ...models.schemas import (
    KnowledgeBase,
    Document,
    QueryRequest,
    QueryResponse,
    APIResponse,
    PaginatedResponse,
    UsageStats
)
from ...services.knowledge_base_service import KnowledgeBaseService
from ...services.auth_service import get_current_user
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# 依赖注入
async def get_kb_service() -> KnowledgeBaseService:
    """获取知识库服务"""
    return KnowledgeBaseService()


@router.post("", response_model=APIResponse)
async def create_knowledge_base(
    kb_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    创建知识库

    创建一个新的知识库，用户将成为所有者。
    """
    try:
        # 添加所有者信息
        kb_data["owner_id"] = current_user.id

        kb = KnowledgeBase(**kb_data)
        created_kb = await kb_service.create_knowledge_base(kb)

        logger.info(
            "知识库创建成功",
            kb_id=created_kb.id,
            kb_name=created_kb.name,
            owner=current_user.username
        )

        return APIResponse(
            success=True,
            message="知识库创建成功",
            data=created_kb.dict()
        )

    except Exception as e:
        logger.error("创建知识库失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@router.get("", response_model=PaginatedResponse)
async def list_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    owner_only: bool = Query(False, description="仅显示自己的知识库"),
    public_only: bool = Query(False, description="仅显示公开的知识库"),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    获取知识库列表

    支持分页、搜索和过滤功能。
    """
    try:
        filters = {}

        if owner_only:
            filters["owner_id"] = current_user.id
        elif public_only:
            filters["is_public"] = True
        elif current_user.role not in ["admin", "knowledge_manager"]:
            # 普通用户只能看到自己的和公开的知识库
            filters["$or"] = [
                {"owner_id": current_user.id},
                {"is_public": True},
                {"collaborators": {"$in": [current_user.id]}}
            ]

        if search:
            filters["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search]}}
            ]

        result = await kb_service.list_knowledge_bases(
            page=page,
            size=size,
            filters=filters
        )

        return result

    except Exception as e:
        logger.error("获取知识库列表失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取知识库列表失败")


@router.get("/{kb_id}", response_model=APIResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    获取知识库详情

    返回指定知识库的详细信息。
    """
    try:
        kb = await kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        return APIResponse(
            success=True,
            message="获取知识库成功",
            data=kb.dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取知识库失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取知识库失败")


@router.put("/{kb_id}", response_model=APIResponse)
async def update_knowledge_base(
    kb_id: str,
    update_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    更新知识库

    更新知识库的名称、描述、设置等信息。
    """
    try:
        # 检查管理权限
        if not await kb_service.check_manage_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限管理此知识库")

        updated_kb = await kb_service.update_knowledge_base(kb_id, update_data)

        logger.info(
            "知识库更新成功",
            kb_id=kb_id,
            operator=current_user.username
        )

        return APIResponse(
            success=True,
            message="知识库更新成功",
            data=updated_kb.dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新知识库失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="更新知识库失败")


@router.delete("/{kb_id}", response_model=APIResponse)
async def delete_knowledge_base(
    kb_id: str,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    删除知识库

    删除指定的知识库及其所有数据。此操作不可逆。
    """
    try:
        # 检查所有者权限
        kb = await kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        if kb.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="只有所有者或管理员可以删除知识库")

        await kb_service.delete_knowledge_base(kb_id)

        logger.info(
            "知识库删除成功",
            kb_id=kb_id,
            kb_name=kb.name,
            operator=current_user.username
        )

        return APIResponse(
            success=True,
            message="知识库删除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除知识库失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="删除知识库失败")


@router.post("/{kb_id}/documents", response_model=APIResponse)
async def add_document_to_kb(
    kb_id: str,
    document_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    向知识库添加文档

    将文档添加到指定的知识库中。
    """
    try:
        # 检查写入权限
        if not await kb_service.check_write_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限向此知识库添加文档")

        # 添加关联信息
        document_data["knowledge_base_id"] = kb_id
        document_data["user_id"] = current_user.id

        document = Document(**document_data)
        result = await kb_service.add_document(kb_id, document)

        logger.info(
            "文档添加成功",
            kb_id=kb_id,
            doc_id=document.id,
            filename=document.filename,
            user=current_user.username
        )

        return APIResponse(
            success=True,
            message="文档添加成功",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("添加文档失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="添加文档失败")


@router.get("/{kb_id}/documents", response_model=PaginatedResponse)
async def list_kb_documents(
    kb_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="文档状态"),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    获取知识库文档列表

    返回指定知识库中的所有文档。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        filters = {"knowledge_base_id": kb_id}

        if search:
            filters["$or"] = [
                {"filename": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search]}}
            ]

        if status:
            filters["status"] = status

        result = await kb_service.list_documents(
            page=page,
            size=size,
            filters=filters
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取文档列表失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取文档列表失败")


@router.post("/{kb_id}/query", response_model=QueryResponse)
async def query_knowledge_base(
    kb_id: str,
    query_request: QueryRequest,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    查询知识库

    在指定知识库中进行智能问答。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        # 设置知识库过滤
        if not query_request.filters:
            query_request.filters = {}
        query_request.filters["knowledge_base_id"] = kb_id
        query_request.user_id = current_user.id

        response = await kb_service.query_knowledge_base(kb_id, query_request)

        logger.info(
            "知识库查询完成",
            kb_id=kb_id,
            query=query_request.query[:50],
            user=current_user.username,
            response_time=response.response_time
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("知识库查询失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="知识库查询失败")


@router.post("/{kb_id}/query/stream")
async def stream_query_knowledge_base(
    kb_id: str,
    query_request: QueryRequest,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    流式查询知识库

    在指定知识库中进行流式智能问答。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        # 设置知识库过滤
        if not query_request.filters:
            query_request.filters = {}
        query_request.filters["knowledge_base_id"] = kb_id
        query_request.user_id = current_user.id

        async def generate_response():
            async for chunk in kb_service.stream_query_knowledge_base(kb_id, query_request):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("流式查询失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="流式查询失败")


@router.get("/{kb_id}/statistics", response_model=APIResponse)
async def get_kb_statistics(
    kb_id: str,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    获取知识库统计信息

    返回知识库的文档数量、实体数量、关系数量等统计信息。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        stats = await kb_service.get_knowledge_base_statistics(kb_id)

        return APIResponse(
            success=True,
            message="获取统计信息成功",
            data=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取统计信息失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.post("/{kb_id}/collaborators", response_model=APIResponse)
async def add_collaborator(
    kb_id: str,
    collaborator_data: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    添加协作者

    向知识库添加协作者，协作者可以查看和编辑知识库。
    """
    try:
        # 检查管理权限
        if not await kb_service.check_manage_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限管理此知识库")

        user_id = collaborator_data.get("user_id")
        permissions = collaborator_data.get("permissions", ["read"])

        result = await kb_service.add_collaborator(kb_id, user_id, permissions)

        logger.info(
            "协作者添加成功",
            kb_id=kb_id,
            collaborator_id=user_id,
            permissions=permissions,
            operator=current_user.username
        )

        return APIResponse(
            success=True,
            message="协作者添加成功",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("添加协作者失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="添加协作者失败")


@router.delete("/{kb_id}/collaborators/{user_id}", response_model=APIResponse)
async def remove_collaborator(
    kb_id: str,
    user_id: str,
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    移除协作者

    从知识库中移除指定的协作者。
    """
    try:
        # 检查管理权限
        if not await kb_service.check_manage_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限管理此知识库")

        await kb_service.remove_collaborator(kb_id, user_id)

        logger.info(
            "协作者移除成功",
            kb_id=kb_id,
            collaborator_id=user_id,
            operator=current_user.username
        )

        return APIResponse(
            success=True,
            message="协作者移除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("移除协作者失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="移除协作者失败")


@router.post("/{kb_id}/export", response_model=APIResponse)
async def export_knowledge_base(
    kb_id: str,
    export_config: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    导出知识库

    将知识库导出为指定格式的文件。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        export_task = await kb_service.export_knowledge_base(kb_id, export_config, current_user.id)

        logger.info(
            "知识库导出任务已创建",
            kb_id=kb_id,
            task_id=export_task["task_id"],
            user=current_user.username
        )

        return APIResponse(
            success=True,
            message="导出任务已创建",
            data=export_task
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建导出任务失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="创建导出任务失败")


@router.get("/{kb_id}/usage", response_model=APIResponse)
async def get_kb_usage_stats(
    kb_id: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    获取知识库使用统计

    返回指定时间范围内的知识库使用统计数据。
    """
    try:
        # 检查访问权限
        if not await kb_service.check_access_permission(kb_id, current_user.id):
            raise HTTPException(status_code=403, detail="无权限访问此知识库")

        usage_stats = await kb_service.get_usage_statistics(
            kb_id=kb_id,
            start_date=start_date,
            end_date=end_date
        )

        return APIResponse(
            success=True,
            message="获取使用统计成功",
            data=usage_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取使用统计失败", kb_id=kb_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取使用统计失败")