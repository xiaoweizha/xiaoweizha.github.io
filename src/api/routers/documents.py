"""
文档管理路由

文档上传、处理和管理相关接口。
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid
import os
from pathlib import Path
import aiofiles

from ...utils.logger import get_logger
from ...utils.config import get_config
from ...models.schemas import Document, DocumentStatus
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
    request: Request,
    file: UploadFile = File(...)
    # TODO: Re-enable authentication in production
    # current_user: UserInfo = Depends(get_current_user)
):
    """上传文档"""
    try:
        config = get_config()

        # 检查文件类型
        allowed_extensions = [".pdf", ".docx", ".doc", ".txt", ".md", ".html"]
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )

        # 检查文件大小
        max_size = config.storage.max_file_size
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({max_size // (1024*1024)}MB)"
            )

        # 生成文档ID和文件路径
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{file.filename}"

        # 创建存储目录
        storage_path = Path(config.storage.local_base_path)
        storage_path.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = storage_path / safe_filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # 创建文档对象
        document = Document(
            id=doc_id,
            filename=file.filename,
            title=Path(file.filename).stem,  # 文件名作为标题
            file_path=str(file_path),
            file_size=len(content),
            mime_type=file.content_type,
            status=DocumentStatus.PROCESSING,
            author="anonymous",  # TODO: Use actual user when auth is enabled
            metadata={
                "uploaded_by": "anonymous",  # TODO: Use actual user when auth is enabled
                "original_filename": file.filename,
                "extension": file_extension
            }
        )

        # 获取RAG引擎并处理文档
        rag_engine = request.app.state.rag_engine

        # 异步处理文档（在后台）
        import asyncio
        asyncio.create_task(process_document_background(rag_engine, document))

        logger.info(
            "文档上传成功",
            document_id=doc_id,
            filename=file.filename,
            file_size=len(content),
            user="anonymous"  # TODO: Use actual user when auth is enabled
        )

        return UploadResponse(
            document_id=doc_id,
            message="文档上传成功，正在处理中"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("文档上传失败", error=str(e), filename=file.filename if file else None)
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


async def process_document_background(rag_engine, document: Document):
    """在后台处理文档"""
    try:
        logger.info("开始处理文档", document_id=document.id, filename=document.filename)

        # 使用RAG引擎处理文档
        result = await rag_engine.add_document(document, build_graph=True)

        logger.info(
            "文档处理完成",
            document_id=document.id,
            chunks_count=result.get("chunks_count", 0),
            entities=result.get("graph_entities", 0),
            relations=result.get("graph_relations", 0)
        )

        # 更新文档状态为完成
        # TODO: 在实际应用中，这里应该更新数据库中的文档状态

    except Exception as e:
        logger.error(
            "文档处理失败",
            document_id=document.id,
            filename=document.filename,
            error=str(e)
        )
        # TODO: 更新文档状态为失败


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
            user="anonymous"  # TODO: Use actual user when auth is enabled
        )

        return {"message": "文档删除成功"}

    except Exception as e:
        logger.error("删除文档失败", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="删除文档失败")