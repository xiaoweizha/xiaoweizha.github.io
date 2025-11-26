"""
RAG引擎核心模块

基于LightRAG架构的企业级RAG引擎实现。
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import structlog

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .graph_store import GraphStore
from .retriever import HybridRetriever
from .generator import ResponseGenerator
from ..utils.config import get_config
from ..utils.logger import get_logger
from ..models.schemas import (
    Document,
    QueryRequest,
    QueryResponse
)

logger = get_logger(__name__)


@dataclass
class RAGEngineConfig:
    """RAG引擎配置"""
    retrieval_mode: str = "hybrid"
    top_k: int = 10
    similarity_threshold: float = 0.7
    rerank_enabled: bool = True
    rerank_top_k: int = 5
    context_window: int = 4000
    max_context_tokens: int = 3000
    response_language: str = "zh-CN"
    enable_cache: bool = True
    cache_ttl: int = 3600


class RAGEngine:
    """
    企业级RAG引擎

    集成文档处理、向量检索、知识图谱、混合检索和智能生成功能。
    """

    def __init__(self, config: Optional[RAGEngineConfig] = None):
        """
        初始化RAG引擎

        Args:
            config: RAG引擎配置
        """
        self.config = config or RAGEngineConfig()
        self.system_config = get_config()

        # 初始化各个组件
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            graph_store=self.graph_store,
            mode=self.config.retrieval_mode
        )
        self.generator = ResponseGenerator()

        # 缓存
        self._cache: Dict[str, Any] = {}

        logger.info("RAG引擎初始化完成", config=self.config)

    async def initialize(self) -> None:
        """
        异步初始化RAG引擎
        """
        try:
            # 初始化各个组件
            await self.document_processor.initialize()
            await self.vector_store.initialize()
            await self.graph_store.initialize()
            await self.retriever.initialize()
            await self.generator.initialize()

            logger.info("RAG引擎异步初始化完成")

        except Exception as e:
            logger.error("RAG引擎初始化失败", error=str(e))
            raise

    async def add_document(
        self,
        document: Document,
        build_graph: bool = True
    ) -> Dict[str, Any]:
        """
        添加文档到知识库

        Args:
            document: 文档对象
            build_graph: 是否构建知识图谱

        Returns:
            处理结果
        """
        try:
            logger.info(
                "开始处理文档",
                doc_id=document.id,
                filename=document.filename
            )

            # 1. 文档处理和分块
            chunks = await self.document_processor.process_document(document)

            # 2. 向量化并存储
            embeddings = await self.vector_store.add_chunks(chunks)

            # 3. 构建知识图谱（可选）
            graph_result = None
            if build_graph:
                graph_result = await self.graph_store.build_graph_from_chunks(
                    chunks
                )

            # 4. 更新检索器索引
            await self.retriever.update_index()

            # 清除相关缓存
            self._clear_cache()

            result = {
                "document_id": document.id,
                "chunks_count": len(chunks),
                "embeddings_count": len(embeddings),
                "graph_entities": graph_result.get("entities", 0) if graph_result else 0,
                "graph_relations": graph_result.get("relations", 0) if graph_result else 0,
                "status": "success"
            }

            logger.info("文档处理完成", result=result)
            return result

        except Exception as e:
            logger.error(
                "文档处理失败",
                doc_id=document.id,
                error=str(e)
            )
            raise

    async def query(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> QueryResponse:
        """
        执行RAG查询

        Args:
            query: 查询问题
            mode: 检索模式 (local/global/hybrid/naive/mix)
            top_k: 返回top-k结果
            filters: 过滤条件
            user_id: 用户ID（用于权限控制）

        Returns:
            查询响应
        """
        try:
            # 参数处理
            retrieval_mode = mode or self.config.retrieval_mode
            k = top_k or self.config.top_k

            # 生成缓存键
            cache_key = self._generate_cache_key(query, retrieval_mode, k, filters)

            # 检查缓存
            if self.config.enable_cache and cache_key in self._cache:
                logger.info("命中缓存", query=query[:50])
                return self._cache[cache_key]

            logger.info(
                "开始RAG查询",
                query=query[:100],
                mode=retrieval_mode,
                top_k=k
            )

            # 1. 检索相关文档和知识
            retrieval_result = await self.retriever.retrieve(
                query=query,
                mode=retrieval_mode,
                top_k=k,
                filters=filters
            )

            # 2. 重排序（如果启用）
            if self.config.rerank_enabled:
                retrieval_result = await self._rerank_results(
                    query, retrieval_result
                )

            # 3. 构建上下文
            context = self._build_context(retrieval_result)

            # 4. 生成回答
            response = await self.generator.generate_response(
                query=query,
                context=context,
                language=self.config.response_language
            )

            # 5. 构建最终响应
            query_response = QueryResponse(
                query=query,
                answer=response.answer,
                sources=retrieval_result.sources,
                context=context[:500],  # 截断上下文用于显示
                retrieval_mode=retrieval_mode,
                confidence=response.confidence,
                tokens_used=response.tokens_used,
                response_time=response.response_time,
                metadata={
                    "retrieved_chunks": len(retrieval_result.chunks),
                    "graph_entities": len(retrieval_result.entities),
                    "graph_relations": len(retrieval_result.relations)
                }
            )

            # 缓存结果
            if self.config.enable_cache:
                self._cache[cache_key] = query_response

            logger.info(
                "RAG查询完成",
                query=query[:50],
                confidence=response.confidence,
                response_time=response.response_time
            )

            return query_response

        except Exception as e:
            logger.error("RAG查询失败", query=query[:50], error=str(e))
            raise

    async def batch_query(
        self,
        queries: List[str],
        mode: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[QueryResponse]:
        """
        批量查询

        Args:
            queries: 查询列表
            mode: 检索模式
            top_k: 返回top-k结果

        Returns:
            查询响应列表
        """
        tasks = [
            self.query(query, mode, top_k)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "批量查询中单个查询失败",
                    query=queries[i][:50],
                    error=str(result)
                )
                # 创建错误响应
                error_response = QueryResponse(
                    query=queries[i],
                    answer="抱歉，处理您的查询时发生了错误。",
                    sources=[],
                    context="",
                    retrieval_mode=mode or self.config.retrieval_mode,
                    confidence=0.0,
                    tokens_used=0,
                    response_time=0.0,
                    error=str(result)
                )
                responses.append(error_response)
            else:
                responses.append(result)

        return responses

    async def update_document(
        self,
        document_id: str,
        document: Document
    ) -> Dict[str, Any]:
        """
        更新文档

        Args:
            document_id: 文档ID
            document: 新的文档对象

        Returns:
            更新结果
        """
        try:
            # 1. 删除旧文档
            await self.delete_document(document_id)

            # 2. 添加新文档
            result = await self.add_document(document)

            result["operation"] = "update"
            logger.info("文档更新完成", doc_id=document_id)

            return result

        except Exception as e:
            logger.error("文档更新失败", doc_id=document_id, error=str(e))
            raise

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档

        Args:
            document_id: 文档ID

        Returns:
            删除结果
        """
        try:
            # 1. 从向量存储中删除
            vector_result = await self.vector_store.delete_document(document_id)

            # 2. 从图存储中删除
            graph_result = await self.graph_store.delete_document(document_id)

            # 3. 更新检索器索引
            await self.retriever.update_index()

            # 4. 清除缓存
            self._clear_cache()

            result = {
                "document_id": document_id,
                "deleted_chunks": vector_result.get("deleted_chunks", 0),
                "deleted_entities": graph_result.get("deleted_entities", 0),
                "deleted_relations": graph_result.get("deleted_relations", 0),
                "status": "success"
            }

            logger.info("文档删除完成", doc_id=document_id)
            return result

        except Exception as e:
            logger.error("文档删除失败", doc_id=document_id, error=str(e))
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            统计信息
        """
        try:
            # 获取各组件统计
            vector_stats = await self.vector_store.get_statistics()
            graph_stats = await self.graph_store.get_statistics()

            stats = {
                "documents": vector_stats.get("documents", 0),
                "chunks": vector_stats.get("chunks", 0),
                "embeddings": vector_stats.get("embeddings", 0),
                "entities": graph_stats.get("entities", 0),
                "relations": graph_stats.get("relations", 0),
                "cache_size": len(self._cache),
                "last_updated": vector_stats.get("last_updated"),
                "storage_size": {
                    "vector_store": vector_stats.get("storage_size", 0),
                    "graph_store": graph_stats.get("storage_size", 0)
                }
            }

            return stats

        except Exception as e:
            logger.error("获取统计信息失败", error=str(e))
            raise

    async def _rerank_results(
        self,
        query: str,
        retrieval_result: RetrievalResult
    ) -> RetrievalResult:
        """
        重排序检索结果

        Args:
            query: 查询
            retrieval_result: 检索结果

        Returns:
            重排序后的结果
        """
        # 当前返回原始检索结果
        # 生产环境中可集成BGE-reranker等专业重排序模型
        return retrieval_result

    def _build_context(self, retrieval_result: RetrievalResult) -> str:
        """
        构建上下文

        Args:
            retrieval_result: 检索结果

        Returns:
            构建的上下文
        """
        context_parts = []

        # 添加文档块内容
        for chunk in retrieval_result.chunks[:self.config.rerank_top_k]:
            context_parts.append(f"文档片段：{chunk.content}")

        # 添加知识图谱信息
        if retrieval_result.entities:
            entities_str = "、".join([e.name for e in retrieval_result.entities[:5]])
            context_parts.append(f"相关实体：{entities_str}")

        if retrieval_result.relations:
            relations_str = "；".join([
                f"{r.source}-{r.relation}-{r.target}"
                for r in retrieval_result.relations[:3]
            ])
            context_parts.append(f"相关关系：{relations_str}")

        context = "\n\n".join(context_parts)

        # 截断到最大长度
        if len(context) > self.config.max_context_tokens * 4:  # 粗略估算
            context = context[:self.config.max_context_tokens * 4] + "..."

        return context

    def _generate_cache_key(
        self,
        query: str,
        mode: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """
        生成缓存键

        Args:
            query: 查询
            mode: 检索模式
            top_k: top-k值
            filters: 过滤条件

        Returns:
            缓存键
        """
        import hashlib

        key_parts = [query, mode, str(top_k)]
        if filters:
            key_parts.append(str(sorted(filters.items())))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        logger.debug("缓存已清除")

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            # 检查各组件状态
            checks = {
                "document_processor": await self.document_processor.health_check(),
                "vector_store": await self.vector_store.health_check(),
                "graph_store": await self.graph_store.health_check(),
                "retriever": await self.retriever.health_check(),
                "generator": await self.generator.health_check()
            }

            # 判断整体健康状态
            all_healthy = all(check["status"] == "healthy" for check in checks.values())

            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "components": checks,
                "timestamp": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.error("健康检查失败", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }

    async def close(self) -> None:
        """
        关闭RAG引擎，清理资源
        """
        try:
            await self.document_processor.close()
            await self.vector_store.close()
            await self.graph_store.close()
            await self.retriever.close()
            await self.generator.close()

            self._clear_cache()

            logger.info("RAG引擎已关闭")

        except Exception as e:
            logger.error("关闭RAG引擎时发生错误", error=str(e))