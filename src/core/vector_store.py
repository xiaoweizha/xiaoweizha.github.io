"""
向量存储模块

向量数据库的统一接口实现。
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import numpy as np
import asyncio

from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class VectorStoreBase(ABC):
    """向量存储基类"""

    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        pass

    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        pass

    @abstractmethod
    async def delete_vectors(self, ids: List[str]) -> bool:
        """删除向量"""
        pass

    @abstractmethod
    async def get_vector_count(self) -> int:
        """获取向量数量"""
        pass


class QdrantVectorStore(VectorStoreBase):
    """Qdrant向量存储实现"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config().database
        self.client = None
        self.collection_name = self.config.qdrant_collection

    async def initialize(self):
        """初始化连接"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct, CreateCollection

            # 初始化Qdrant客户端
            self.client = QdrantClient(
                host=getattr(self.config, 'qdrant_host', 'localhost'),
                port=getattr(self.config, 'qdrant_port', 6333),
                api_key=getattr(self.config, 'qdrant_api_key', None)
            )

            # 检查集合是否存在，不存在则创建
            collections = await asyncio.to_thread(self.client.get_collections)
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # 默认OpenAI embedding维度
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建Qdrant集合: {self.collection_name}")

            # 测试连接
            await asyncio.to_thread(self.client.get_collection, self.collection_name)

            logger.info("Qdrant向量存储初始化成功")
            return True

        except Exception as e:
            logger.error("Qdrant初始化失败", error=str(e))
            return False

    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量到Qdrant"""
        try:
            if not self.client:
                raise RuntimeError("Qdrant客户端未初始化")

            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            # 构建Qdrant点数据
            from qdrant_client.models import PointStruct

            points = []
            for i, (vector, metadata, point_id) in enumerate(zip(vectors, metadatas, ids)):
                # 确保向量是正确的格式
                if isinstance(vector, np.ndarray):
                    vector = vector.tolist()

                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=metadata
                )
                points.append(point)

            # 批量插入
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"成功添加{len(vectors)}个向量到Qdrant")
            return ids

        except Exception as e:
            logger.error("添加向量失败", error=str(e))
            raise

    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """在Qdrant中搜索向量"""
        try:
            if not self.client:
                raise RuntimeError("Qdrant客户端未初始化")

            # 确保查询向量是正确格式
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()

            # 构建搜索请求
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    # 可以扩展更多过滤条件类型

                if conditions:
                    search_filter = Filter(must=conditions)

            # 执行搜索
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter,
                with_payload=True,
                score_threshold=0.0  # 可以配置最小相似度阈值
            )

            # 转换结果格式
            results = []
            for hit in search_result:
                result = {
                    "id": hit.id,
                    "score": float(hit.score),
                    "metadata": hit.payload if hit.payload else {}
                }
                results.append(result)

            logger.debug(f"向量搜索完成，找到{len(results)}个结果")
            return results

        except Exception as e:
            logger.error("向量搜索失败", error=str(e))
            return []

    async def delete_vectors(self, ids: List[str]) -> bool:
        """从Qdrant删除向量"""
        try:
            if not self.client:
                raise RuntimeError("Qdrant客户端未初始化")

            if not ids:
                return True

            # 批量删除
            await asyncio.to_thread(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=ids
            )

            logger.info(f"成功删除{len(ids)}个向量")
            return True

        except Exception as e:
            logger.error("删除向量失败", error=str(e))
            return False

    async def get_vector_count(self) -> int:
        """获取向量数量"""
        try:
            if not self.client:
                raise RuntimeError("Qdrant客户端未初始化")

            # 获取集合信息
            collection_info = await asyncio.to_thread(
                self.client.get_collection,
                collection_name=self.collection_name
            )

            return collection_info.points_count or 0

        except Exception as e:
            logger.error("获取向量数量失败", error=str(e))
            return 0


class VectorStore:
    """向量存储统一接口"""

    def __init__(self, store_type: str = "qdrant"):
        self.store_type = store_type
        self.store = None

    async def initialize(self):
        """初始化向量存储"""
        try:
            if self.store_type == "qdrant":
                self.store = QdrantVectorStore()
            else:
                raise ValueError(f"不支持的向量存储类型: {self.store_type}")

            success = await self.store.initialize()
            if success:
                logger.info(f"向量存储初始化成功: {self.store_type}")
            else:
                logger.error(f"向量存储初始化失败: {self.store_type}")

            return success

        except Exception as e:
            logger.error("向量存储初始化异常", error=str(e))
            return False

    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加向量"""
        if not self.store:
            raise RuntimeError("向量存储未初始化")
        return await self.store.add_vectors(vectors, metadatas, ids)

    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        if not self.store:
            raise RuntimeError("向量存储未初始化")
        return await self.store.search_vectors(query_vector, top_k, filters)

    async def delete_vectors(self, ids: List[str]) -> bool:
        """删除向量"""
        if not self.store:
            raise RuntimeError("向量存储未初始化")
        return await self.store.delete_vectors(ids)

    async def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        if not self.store:
            return {"status": "未初始化", "count": 0}

        try:
            count = await self.store.get_vector_count()
            return {
                "status": "正常",
                "type": self.store_type,
                "vector_count": count
            }
        except Exception as e:
            logger.error("获取向量存储统计失败", error=str(e))
            return {"status": "异常", "error": str(e)}

    async def add_chunks(self, chunks) -> Dict[str, Any]:
        """
        添加文档块到向量存储

        Args:
            chunks: DocumentChunk 列表

        Returns:
            添加结果
        """
        if not self.store:
            raise RuntimeError("向量存储未初始化")

        try:
            # 准备向量和元数据
            vectors = []
            metadatas = []
            ids = []

            # 导入嵌入模块
            from .embeddings import get_embedding_provider

            embedding_provider = get_embedding_provider()

            for i, chunk in enumerate(chunks):
                # 生成嵌入向量（如果chunk还没有嵌入）
                if not chunk.embedding:
                    embedding = await embedding_provider.embed_text(chunk.content)
                    chunk.embedding = embedding
                else:
                    embedding = chunk.embedding

                vectors.append(embedding)

                # 准备元数据
                metadata = {
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    **chunk.metadata  # 包含原有元数据
                }
                metadatas.append(metadata)

                # 生成唯一ID
                chunk_id = f"{chunk.document_id}_chunk_{chunk.chunk_index}"
                ids.append(chunk_id)

            # 调用底层存储方法
            result_ids = await self.store.add_vectors(vectors, metadatas, ids)

            logger.info(
                "成功添加文档块到向量存储",
                chunks_count=len(chunks),
                document_id=chunks[0].document_id if chunks else None
            )

            return {
                "success": True,
                "chunks_count": len(chunks),
                "vector_ids": result_ids,
                "embeddings_generated": len([c for c in chunks if c.embedding])
            }

        except Exception as e:
            logger.error("添加文档块失败", error=str(e))
            raise

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.store:
                return {"status": "unhealthy", "reason": "未初始化"}

            # 尝试获取统计信息来验证连接
            stats = await self.get_statistics()
            if stats["status"] == "正常":
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "reason": stats.get("error", "未知错误")}

        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}