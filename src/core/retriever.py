"""
混合检索器模块

实现向量检索、图检索和全文检索的混合策略。
"""

from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio

from .vector_store import VectorStore
from .graph_store import GraphStore
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    score: float
    source: str  # vector, graph, fulltext
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None


class RetrieverBase(ABC):
    """检索器基类"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """执行检索"""
        pass


class VectorRetriever(RetrieverBase):
    """向量检索器"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """向量检索"""
        try:
            # 实际的查询向量化
            from .embeddings import get_embedding_provider

            embedding_provider = get_embedding_provider()
            query_vector = await embedding_provider.embed_text(query)

            # 执行向量搜索
            vector_results = await self.vector_store.search_vectors(
                query_vector=query_vector,
                top_k=top_k,
                filters=filters
            )

            # 转换为统一格式
            results = []
            for i, result in enumerate(vector_results):
                metadata = result.get("metadata", {})
                retrieval_result = RetrievalResult(
                    content=metadata.get("content", ""),
                    score=result.get("score", 0.0),
                    source="vector",
                    metadata=metadata,
                    document_id=metadata.get("document_id"),
                    chunk_id=metadata.get("chunk_id", result.get("id"))
                )
                results.append(retrieval_result)

            logger.info(f"向量检索完成，返回{len(results)}个结果")
            return results

        except Exception as e:
            logger.error("向量检索失败", error=str(e))
            return []


class GraphRetriever(RetrieverBase):
    """图检索器"""

    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """图检索"""
        try:
            # TODO: 实际的实体识别和图遍历
            # 1. 从query中提取实体
            # 2. 在知识图谱中查找相关实体和关系
            # 3. 构建检索结果

            # 模拟实体提取
            entities = await self._extract_entities(query)

            results = []
            for entity in entities:
                # 查找相关实体
                related = await self.graph_store.find_related_entities(
                    entity_id=entity["id"],
                    max_depth=2
                )

                for rel in related[:top_k]:
                    result = RetrievalResult(
                        content=f"实体{entity['name']}与{rel['entity_id']}存在{rel['relation_type']}关系",
                        score=rel.get("weight", 0.5),
                        source="graph",
                        metadata={
                            "entity": entity,
                            "related_entity": rel["entity_id"],
                            "relation_type": rel["relation_type"]
                        }
                    )
                    results.append(result)

            logger.info(f"图检索完成，返回{len(results)}个结果")
            return results[:top_k]

        except Exception as e:
            logger.error("图检索失败", error=str(e))
            return []

    async def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """从查询中提取实体"""
        # 简单的关键词匹配实体提取
        entities = []

        # 定义一些常见的技术实体
        entity_keywords = {
            "rag": {"id": "rag_tech", "name": "RAG技术", "type": "Concept"},
            "向量检索": {"id": "vector_search", "name": "向量检索", "type": "Concept"},
            "知识图谱": {"id": "knowledge_graph", "name": "知识图谱", "type": "Concept"},
            "人工智能": {"id": "ai_system", "name": "人工智能", "type": "System"},
            "机器学习": {"id": "machine_learning", "name": "机器学习", "type": "Concept"},
            "深度学习": {"id": "deep_learning", "name": "深度学习", "type": "Concept"}
        }

        query_lower = query.lower()
        for keyword, entity_info in entity_keywords.items():
            if keyword.lower() in query_lower:
                entities.append(entity_info)

        # 如果没找到匹配的实体，返回默认实体
        if not entities:
            entities = [
                {"id": "general_ai", "name": "人工智能", "type": "Concept"},
                {"id": "general_tech", "name": "技术", "type": "Concept"}
            ]

        return entities


class FulltextRetriever(RetrieverBase):
    """全文检索器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config().database

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """全文检索"""
        try:
            # TODO: 实际的Elasticsearch查询
            # 这里返回模拟结果
            results = []

            # 模拟关键词匹配
            keywords = query.split()
            for i, keyword in enumerate(keywords[:top_k]):
                result = RetrievalResult(
                    content=f"包含关键词'{keyword}'的文档内容...",
                    score=0.8 - i * 0.1,
                    source="fulltext",
                    metadata={
                        "keyword": keyword,
                        "document_title": f"文档{i+1}",
                        "highlight": f"...{keyword}..."
                    }
                )
                results.append(result)

            logger.info(f"全文检索完成，返回{len(results)}个结果")
            return results

        except Exception as e:
            logger.error("全文检索失败", error=str(e))
            return []


class HybridRetriever:
    """混合检索器"""

    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        config: Optional[Dict[str, Any]] = None
    ):
        self.vector_retriever = VectorRetriever(vector_store)
        self.graph_retriever = GraphRetriever(graph_store)
        self.fulltext_retriever = FulltextRetriever(config)
        self.config = config or {}

    async def initialize(self) -> None:
        """初始化检索器"""
        try:
            logger.info("混合检索器初始化完成")
        except Exception as e:
            logger.error("混合检索器初始化失败", error=str(e))
            raise

    async def update_index(self) -> None:
        """更新检索索引"""
        try:
            # 这里可以添加索引更新逻辑
            logger.info("检索索引更新完成")
        except Exception as e:
            logger.error("更新检索索引失败", error=str(e))
            raise

    async def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        rerank: bool = True
    ) -> List[RetrievalResult]:
        """
        混合检索

        Args:
            query: 查询文本
            mode: 检索模式 (vector, graph, fulltext, hybrid)
            top_k: 返回结果数量
            rerank: 是否重新排序
        """
        try:
            all_results = []

            if mode == "vector":
                results = await self.vector_retriever.retrieve(query, top_k)
                all_results.extend(results)

            elif mode == "graph":
                results = await self.graph_retriever.retrieve(query, top_k)
                all_results.extend(results)

            elif mode == "fulltext":
                results = await self.fulltext_retriever.retrieve(query, top_k)
                all_results.extend(results)

            elif mode == "hybrid":
                # 并行执行多种检索
                tasks = [
                    self.vector_retriever.retrieve(query, top_k // 3 + 2),
                    self.graph_retriever.retrieve(query, top_k // 3 + 2),
                    self.fulltext_retriever.retrieve(query, top_k // 3 + 2)
                ]

                results_list = await asyncio.gather(*tasks, return_exceptions=True)

                for results in results_list:
                    if isinstance(results, list):
                        all_results.extend(results)

            else:
                raise ValueError(f"不支持的检索模式: {mode}")

            # 去重和重排序
            unique_results = self._deduplicate_results(all_results)

            if rerank and len(unique_results) > 1:
                unique_results = await self._rerank_results(query, unique_results)

            # 返回top_k结果
            final_results = unique_results[:top_k]

            logger.info(
                f"混合检索完成",
                mode=mode,
                total_results=len(all_results),
                unique_results=len(unique_results),
                final_results=len(final_results)
            )

            return final_results

        except Exception as e:
            logger.error("混合检索失败", error=str(e))
            return []

    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重检索结果"""
        seen_content = set()
        unique_results = []

        for result in results:
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        return unique_results

    async def _rerank_results(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """重新排序结果"""
        try:
            # 实现基于多个因子的重排序逻辑
            from .embeddings import get_embedding_provider

            # 获取查询嵌入用于更精确的相似度计算
            embedding_provider = get_embedding_provider()
            query_embedding = await embedding_provider.embed_text(query)

            for result in results:
                # 保存原始分数
                original_score = result.score

                # 1. 根据来源调整权重
                source_weight = 1.0
                if result.source == "vector":
                    source_weight = 1.0
                elif result.source == "graph":
                    source_weight = 0.9
                elif result.source == "fulltext":
                    source_weight = 0.8

                # 2. 根据内容质量调整分数
                content = result.content
                content_length = len(content)

                # 内容长度评分 (适中长度得分更高)
                if 50 <= content_length <= 500:
                    length_bonus = 1.1
                elif content_length > 500:
                    length_bonus = 1.05
                else:
                    length_bonus = 0.9

                # 3. 关键词匹配评分
                query_words = set(query.lower().split())
                content_words = set(content.lower().split())
                keyword_overlap = len(query_words.intersection(content_words))
                keyword_bonus = 1.0 + (keyword_overlap * 0.1)

                # 4. 计算与查询的语义相似度 (如果内容较长值得计算)
                semantic_bonus = 1.0
                if content_length > 20:
                    try:
                        content_embedding = await embedding_provider.embed_text(content[:500])  # 截断长文本
                        semantic_similarity = self._cosine_similarity(query_embedding, content_embedding)
                        semantic_bonus = 1.0 + (semantic_similarity * 0.5)
                    except:
                        # 如果计算失败，使用默认值
                        semantic_bonus = 1.0

                # 5. 综合评分
                final_score = original_score * source_weight * length_bonus * keyword_bonus * semantic_bonus

                # 更新分数，但保留原始分数供参考
                result.metadata["original_score"] = original_score
                result.metadata["rerank_factors"] = {
                    "source_weight": source_weight,
                    "length_bonus": length_bonus,
                    "keyword_bonus": keyword_bonus,
                    "semantic_bonus": semantic_bonus
                }
                result.score = final_score

            # 按最终分数排序
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

            logger.info(f"重排序完成，调整了{len(results)}个结果")
            return sorted_results

        except Exception as e:
            logger.error("重排序失败", error=str(e))
            return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            import numpy as np

            v1 = np.array(vec1)
            v2 = np.array(vec2)

            # 计算余弦相似度
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return max(-1.0, min(1.0, similarity))  # 确保在[-1, 1]范围内

        except:
            return 0.0

    async def get_statistics(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        try:
            vector_stats = await self.vector_retriever.vector_store.get_statistics()
            graph_stats = await self.graph_retriever.graph_store.get_statistics()

            return {
                "vector_store": vector_stats,
                "graph_store": graph_stats,
                "retrieval_modes": ["vector", "graph", "fulltext", "hybrid"]
            }

        except Exception as e:
            logger.error("获取检索器统计失败", error=str(e))
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            vector_health = await self.vector_retriever.vector_store.health_check()
            graph_health = await self.graph_retriever.graph_store.health_check()

            all_healthy = (
                vector_health["status"] == "healthy" and
                graph_health["status"] == "healthy"
            )

            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "components": {
                    "vector_retriever": vector_health,
                    "graph_retriever": graph_health,
                    "fulltext_retriever": {"status": "healthy"}
                }
            }
        except Exception as e:
            logger.error("检索器健康检查失败", error=str(e))
            return {"status": "error", "error": str(e)}

    async def close(self) -> None:
        """关闭检索器，清理资源"""
        try:
            # 这里可以添加资源清理逻辑
            logger.info("检索器已关闭")
        except Exception as e:
            logger.error("关闭检索器时发生错误", error=str(e))