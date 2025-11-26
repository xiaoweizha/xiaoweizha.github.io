"""
知识库服务

处理知识库相关的业务逻辑。
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from ..utils.logger import get_logger
from ..models.schemas import (
    KnowledgeBase,
    Document,
    QueryRequest,
    QueryResponse,
    DocumentStatus
)

logger = get_logger(__name__)


class KnowledgeBaseService:
    """知识库服务类"""

    def __init__(self):
        self.knowledge_bases = {}  # 临时存储，生产环境应该使用数据库
        self.documents = {}  # 临时存储

    async def create_knowledge_base(self, name: str, description: str = "", user_id: str = "") -> KnowledgeBase:
        """创建知识库"""
        try:
            kb_id = f"kb_{len(self.knowledge_bases) + 1}"
            kb = KnowledgeBase(
                id=kb_id,
                name=name,
                description=description,
                owner_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.knowledge_bases[kb_id] = kb
            logger.info(f"创建知识库成功: {name}", kb_id=kb_id)
            return kb

        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            raise

    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self.knowledge_bases.get(kb_id)

    async def list_knowledge_bases(self, user_id: str = "", page: int = 1, size: int = 20) -> List[KnowledgeBase]:
        """列出知识库"""
        try:
            all_kbs = list(self.knowledge_bases.values())

            # 如果指定了用户，只返回该用户的知识库
            if user_id:
                all_kbs = [kb for kb in all_kbs if kb.owner_id == user_id]

            # 分页
            start = (page - 1) * size
            end = start + size

            return all_kbs[start:end]

        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []

    async def update_knowledge_base(self, kb_id: str, updates: Dict[str, Any]) -> Optional[KnowledgeBase]:
        """更新知识库"""
        try:
            kb = self.knowledge_bases.get(kb_id)
            if not kb:
                return None

            # 更新字段
            for key, value in updates.items():
                if hasattr(kb, key):
                    setattr(kb, key, value)

            kb.updated_at = datetime.utcnow()
            logger.info(f"更新知识库成功: {kb_id}")
            return kb

        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            raise

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            if kb_id in self.knowledge_bases:
                del self.knowledge_bases[kb_id]

                # 删除相关文档
                docs_to_delete = [doc_id for doc_id, doc in self.documents.items()
                                 if doc.knowledge_base_id == kb_id]
                for doc_id in docs_to_delete:
                    del self.documents[doc_id]

                logger.info(f"删除知识库成功: {kb_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"删除知识库失败: {e}")
            return False

    async def upload_document(self, kb_id: str, file_name: str, content: str, metadata: Dict[str, Any] = None) -> Document:
        """上传文档到知识库"""
        try:
            if kb_id not in self.knowledge_bases:
                raise ValueError(f"知识库不存在: {kb_id}")

            doc_id = f"doc_{len(self.documents) + 1}"
            doc = Document(
                id=doc_id,
                knowledge_base_id=kb_id,
                title=file_name,
                content=content,
                file_name=file_name,
                file_size=len(content.encode('utf-8')),
                mime_type="text/plain",
                status=DocumentStatus.PENDING,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.documents[doc_id] = doc

            # 异步处理文档（简化版本）
            asyncio.create_task(self._process_document(doc_id))

            logger.info(f"文档上传成功: {file_name}", doc_id=doc_id, kb_id=kb_id)
            return doc

        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            raise

    async def _process_document(self, doc_id: str):
        """处理文档（模拟）"""
        try:
            doc = self.documents.get(doc_id)
            if not doc:
                return

            # 模拟处理时间
            await asyncio.sleep(1)

            # 更新状态为已完成
            doc.status = DocumentStatus.COMPLETED
            doc.processed_at = datetime.utcnow()
            doc.updated_at = datetime.utcnow()

            logger.info(f"文档处理完成: {doc_id}")

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            if doc_id in self.documents:
                self.documents[doc_id].status = DocumentStatus.FAILED

    async def list_documents(self, kb_id: str, page: int = 1, size: int = 20) -> List[Document]:
        """获取知识库中的文档列表"""
        try:
            kb_docs = [doc for doc in self.documents.values()
                      if doc.knowledge_base_id == kb_id]

            # 按创建时间排序
            kb_docs.sort(key=lambda x: x.created_at, reverse=True)

            # 分页
            start = (page - 1) * size
            end = start + size

            return kb_docs[start:end]

        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档详情"""
        return self.documents.get(doc_id)

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            if doc_id in self.documents:
                del self.documents[doc_id]
                logger.info(f"删除文档成功: {doc_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    async def search_knowledge_base(self, kb_id: str, query: str, mode: str = "hybrid", top_k: int = 5) -> Dict[str, Any]:
        """在知识库中搜索"""
        try:
            # 简化的搜索逻辑
            kb_docs = [doc for doc in self.documents.values()
                      if doc.knowledge_base_id == kb_id and doc.status == DocumentStatus.COMPLETED]

            results = []
            query_lower = query.lower()

            for doc in kb_docs:
                score = 0.0

                # 标题匹配
                if query_lower in doc.title.lower():
                    score += 1.0

                # 内容匹配
                if query_lower in doc.content.lower():
                    score += 0.5

                if score > 0:
                    results.append({
                        "document_id": doc.id,
                        "title": doc.title,
                        "content": doc.content[:200] + "...",  # 截取前200字符
                        "score": score,
                        "metadata": doc.metadata
                    })

            # 按分数排序
            results.sort(key=lambda x: x["score"], reverse=True)

            return {
                "results": results[:top_k],
                "total": len(results),
                "query": query,
                "mode": mode
            }

        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {"results": [], "total": 0, "query": query, "mode": mode}

    async def get_statistics(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            kb = self.knowledge_bases.get(kb_id)
            if not kb:
                return {}

            kb_docs = [doc for doc in self.documents.values()
                      if doc.knowledge_base_id == kb_id]

            stats = {
                "knowledge_base": {
                    "id": kb_id,
                    "name": kb.name,
                    "created_at": kb.created_at
                },
                "documents": {
                    "total": len(kb_docs),
                    "completed": len([d for d in kb_docs if d.status == DocumentStatus.COMPLETED]),
                    "processing": len([d for d in kb_docs if d.status == DocumentStatus.PROCESSING]),
                    "failed": len([d for d in kb_docs if d.status == DocumentStatus.FAILED])
                },
                "storage": {
                    "total_size": sum(d.file_size for d in kb_docs),
                    "avg_size": sum(d.file_size for d in kb_docs) / len(kb_docs) if kb_docs else 0
                }
            }

            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}