"""
文档管理路由

文档上传、处理和管理相关接口。
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid

from ...utils.logger import get_logger
from .auth import get_current_user, UserInfo

router = APIRouter()
logger = get_logger(__name__)


class DocumentInfo(BaseModel):
    """文档信息"""
    id: str
    title: str
    filename: str
    file_size: int
    mime_type: str
    status: str
    created_at: float
    processed_at: Optional[float] = None


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentInfo]
    total: int
    page: int
    size: int


class UploadResponse(BaseModel):
    """上传响应"""
    document_id: str
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user)
):
    """上传文档"""
    try:
        # 检查文件类型
        allowed_types = ["application/pdf", "application/msword",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "text/plain", "text/markdown"]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )

        # 检查文件大小 (最大50MB)
        max_size = 50 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="文件大小超过限制 (50MB)"
            )

        # 生成文档ID
        doc_id = str(uuid.uuid4())

        # TODO: 实际的文件处理逻辑
        # 1. 保存文件到存储系统
        # 2. 提交到文档处理队列
        # 3. 更新数据库记录

        logger.info(
            "文档上传成功",
            document_id=doc_id,
            filename=file.filename,
            file_size=len(content),
            user=current_user.username
        )

        return UploadResponse(
            document_id=doc_id,
            message="文档上传成功，正在处理中"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("文档上传失败", error=str(e))
        raise HTTPException(status_code=500, detail="文档上传失败")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取文档列表"""
    try:
        # TODO: 从数据库获取实际的文档列表
        # 这里返回模拟数据
        mock_documents = [
            DocumentInfo(
                id="doc1",
                title="RAG技术介绍",
                filename="rag_intro.pdf",
                file_size=1024000,
                mime_type="application/pdf",
                status="processed",
                created_at=time.time() - 3600,
                processed_at=time.time() - 3500
            ),
            DocumentInfo(
                id="doc2",
                title="企业知识库搭建指南",
                filename="kb_guide.docx",
                file_size=2048000,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                status="processing",
                created_at=time.time() - 1800
            )
        ]

        # 过滤状态
        if status:
            mock_documents = [doc for doc in mock_documents if doc.status == status]

        # 分页
        start = (page - 1) * size
        end = start + size
        paginated_docs = mock_documents[start:end]

        return DocumentListResponse(
            documents=paginated_docs,
            total=len(mock_documents),
            page=page,
            size=size
        )

    except Exception as e:
        logger.error("获取文档列表失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取文档列表失败")


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取文档详情"""
    try:
        # TODO: 从数据库获取实际的文档信息
        if document_id == "doc1":
            return DocumentInfo(
                id="doc1",
                title="RAG技术介绍",
                filename="rag_intro.pdf",
                file_size=1024000,
                mime_type="application/pdf",
                status="processed",
                created_at=time.time() - 3600,
                processed_at=time.time() - 3500
            )
        else:
            raise HTTPException(status_code=404, detail="文档不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取文档详情失败", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取文档详情失败")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """删除文档"""
    try:
        # TODO: 实际的删除逻辑
        # 1. 检查文档是否存在
        # 2. 检查用户权限
        # 3. 删除文件和数据库记录
        # 4. 清理相关索引

        logger.info(
            "文档删除成功",
            document_id=document_id,
            user=current_user.username
        )

        return {"message": "文档删除成功"}

    except Exception as e:
        logger.error("删除文档失败", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="删除文档失败")