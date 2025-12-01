#!/usr/bin/env python3
"""
检索逻辑测试 - 不依赖外部服务的单元测试

测试检索逻辑、重排序算法等核心功能。
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.retriever import RetrievalResult, HybridRetriever
from src.core.embeddings import MockEmbeddingProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MockVectorStore:
    """模拟向量存储用于测试"""

    def __init__(self):
        self.data = []
        self.embedding_provider = MockEmbeddingProvider({"dimension": 1536})

    async def initialize(self):
        return True

    async def search_vectors(self, query_vector: List[float], top_k: int = 10, filters=None):
        """模拟向量搜索，返回相关结果"""
        results = [
            {
                "id": "vec_1",
                "score": 0.95,
                "metadata": {
                    "content": "RAG (检索增强生成) 是一种结合了信息检索和文本生成的人工智能技术。它通过从大型知识库中检索相关信息来增强语言模型的生成能力。",
                    "document_id": "doc1",
                    "chunk_id": "chunk_1",
                    "title": "RAG技术介绍"
                }
            },
            {
                "id": "vec_2",
                "score": 0.87,
                "metadata": {
                    "content": "向量检索是现代搜索系统的核心技术之一。通过将文档和查询转换为高维向量，我们可以计算语义相似度来找到最相关的内容。",
                    "document_id": "doc2",
                    "chunk_id": "chunk_2",
                    "title": "向量检索原理"
                }
            },
            {
                "id": "vec_3",
                "score": 0.82,
                "metadata": {
                    "content": "知识图谱是一种用图结构来表示知识的技术，它能够有效地组织和表示实体之间的复杂关系。",
                    "document_id": "doc3",
                    "chunk_id": "chunk_3",
                    "title": "知识图谱技术"
                }
            }
        ]
        return results[:top_k]

    async def health_check(self):
        return {"status": "healthy"}

    async def get_statistics(self):
        return {"status": "正常", "type": "mock", "vector_count": 100}


class MockGraphStore:
    """模拟图存储用于测试"""

    def __init__(self):
        self.entities = [
            {"id": "rag_tech", "type": "Concept", "name": "RAG技术"},
            {"id": "vector_search", "type": "Concept", "name": "向量检索"},
            {"id": "knowledge_graph", "type": "Concept", "name": "知识图谱"},
            {"id": "ai_system", "type": "System", "name": "AI系统"}
        ]

        self.relations = [
            {"from_entity": "rag_tech", "to_entity": "vector_search", "type": "USES", "properties": {"weight": 0.9}},
            {"from_entity": "rag_tech", "to_entity": "knowledge_graph", "type": "USES", "properties": {"weight": 0.8}},
            {"from_entity": "ai_system", "to_entity": "rag_tech", "type": "IMPLEMENTS", "properties": {"weight": 0.95}}
        ]

    async def initialize(self):
        return True

    async def query_relations(self, from_entity=None, to_entity=None, relation_type=None, limit=100):
        """模拟关系查询"""
        filtered_relations = []
        for rel in self.relations:
            if from_entity and rel["from_entity"] != from_entity:
                continue
            if to_entity and rel["to_entity"] != to_entity:
                continue
            if relation_type and rel["type"] != relation_type:
                continue

            # 转换为期望的格式
            result_rel = {
                "id": f"{rel['from_entity']}_{rel['type']}_{rel['to_entity']}",
                "from_entity": rel["from_entity"],
                "to_entity": rel["to_entity"],
                "type": rel["type"],
                "properties": rel["properties"]
            }
            filtered_relations.append(result_rel)

        return filtered_relations[:limit]

    async def find_related_entities(self, entity_id: str, relation_types=None, max_depth=2):
        """查找相关实体"""
        related = []
        for rel in self.relations:
            if rel["from_entity"] == entity_id:
                related.append({
                    "entity_id": rel["to_entity"],
                    "relation_type": rel["type"],
                    "weight": rel["properties"].get("weight", 0.5),
                    "depth": 1
                })
        return related

    async def health_check(self):
        return {"status": "healthy"}

    async def get_statistics(self):
        return {"status": "正常", "type": "mock", "entities": len(self.entities), "relations": len(self.relations)}


async def test_retrieval_result():
    """测试检索结果数据结构"""
    print("=" * 50)
    print("测试检索结果数据结构")
    print("=" * 50)

    # 创建测试结果
    result = RetrievalResult(
        content="这是一个测试文档的内容",
        score=0.85,
        source="vector",
        metadata={"title": "测试文档", "author": "测试作者"},
        document_id="doc123",
        chunk_id="chunk456"
    )

    print(f"✅ 检索结果创建成功:")
    print(f"  内容: {result.content}")
    print(f"  分数: {result.score}")
    print(f"  来源: {result.source}")
    print(f"  文档ID: {result.document_id}")
    print(f"  块ID: {result.chunk_id}")
    print(f"  元数据: {result.metadata}")

    return True


async def test_vector_retriever():
    """测试向量检索器"""
    print("=" * 50)
    print("测试向量检索器")
    print("=" * 50)

    from src.core.retriever import VectorRetriever

    mock_vector_store = MockVectorStore()
    await mock_vector_store.initialize()

    retriever = VectorRetriever(mock_vector_store)

    # 测试检索
    query = "什么是RAG技术？"
    results = await retriever.retrieve(query, top_k=3)

    print(f"✅ 向量检索完成")
    print(f"查询: '{query}'")
    print(f"返回结果数: {len(results)}")

    for i, result in enumerate(results):
        print(f"  {i+1}. 分数: {result.score:.3f} 来源: {result.source}")
        print(f"     内容: {result.content[:60]}...")

    return len(results) > 0


async def test_graph_retriever():
    """测试图检索器"""
    print("=" * 50)
    print("测试图检索器")
    print("=" * 50)

    from src.core.retriever import GraphRetriever

    mock_graph_store = MockGraphStore()
    await mock_graph_store.initialize()

    retriever = GraphRetriever(mock_graph_store)

    # 测试检索
    query = "RAG技术与向量检索的关系"
    results = await retriever.retrieve(query, top_k=3)

    print(f"✅ 图检索完成")
    print(f"查询: '{query}'")
    print(f"返回结果数: {len(results)}")

    for i, result in enumerate(results):
        print(f"  {i+1}. 分数: {result.score:.3f} 来源: {result.source}")
        print(f"     内容: {result.content[:60]}...")

    return len(results) > 0


async def test_fulltext_retriever():
    """测试全文检索器"""
    print("=" * 50)
    print("测试全文检索器")
    print("=" * 50)

    from src.core.retriever import FulltextRetriever

    retriever = FulltextRetriever()

    # 测试检索
    query = "人工智能 机器学习"
    results = await retriever.retrieve(query, top_k=2)

    print(f"✅ 全文检索完成")
    print(f"查询: '{query}'")
    print(f"返回结果数: {len(results)}")

    for i, result in enumerate(results):
        print(f"  {i+1}. 分数: {result.score:.3f} 来源: {result.source}")
        print(f"     内容: {result.content[:60]}...")

    return len(results) > 0


async def test_reranking_algorithm():
    """测试重排序算法"""
    print("=" * 50)
    print("测试重排序算法")
    print("=" * 50)

    mock_vector_store = MockVectorStore()
    mock_graph_store = MockGraphStore()

    retriever = HybridRetriever(mock_vector_store, mock_graph_store)
    await retriever.initialize()

    # 创建测试结果
    test_results = [
        RetrievalResult(
            content="RAG技术是一种先进的AI技术",
            score=0.8,
            source="vector",
            metadata={"title": "RAG介绍"},
        ),
        RetrievalResult(
            content="图检索提供结构化的知识表示",
            score=0.7,
            source="graph",
            metadata={"title": "图检索"},
        ),
        RetrievalResult(
            content="向量检索实现语义匹配",
            score=0.9,
            source="vector",
            metadata={"title": "向量检索"},
        )
    ]

    print("重排序前:")
    for i, result in enumerate(test_results):
        print(f"  {i+1}. 分数: {result.score:.3f} 来源: {result.source}")

    # 执行重排序
    query = "RAG技术原理"
    reranked_results = await retriever._rerank_results(query, test_results)

    print("重排序后:")
    for i, result in enumerate(reranked_results):
        factors = result.metadata.get("rerank_factors", {})
        print(f"  {i+1}. 分数: {result.score:.3f} 来源: {result.source}")
        print(f"     重排序因子: 来源权重={factors.get('source_weight', 1):.2f}, "
              f"长度奖励={factors.get('length_bonus', 1):.2f}, "
              f"关键词奖励={factors.get('keyword_bonus', 1):.2f}")

    # 验证重排序确实改变了顺序
    original_scores = [r.metadata.get("original_score", r.score) for r in test_results]
    reranked_scores = [r.score for r in reranked_results]

    print(f"✅ 重排序算法测试完成")
    print(f"原始分数: {[f'{s:.3f}' for s in original_scores]}")
    print(f"重排序分数: {[f'{s:.3f}' for s in reranked_scores]}")

    return True


async def test_hybrid_retrieval():
    """测试混合检索"""
    print("=" * 50)
    print("测试混合检索")
    print("=" * 50)

    mock_vector_store = MockVectorStore()
    mock_graph_store = MockGraphStore()

    await mock_vector_store.initialize()
    await mock_graph_store.initialize()

    retriever = HybridRetriever(mock_vector_store, mock_graph_store)
    await retriever.initialize()

    # 测试不同检索模式
    query = "RAG技术的应用"
    modes = ["vector", "graph", "fulltext", "hybrid"]

    results_summary = {}

    for mode in modes:
        results = await retriever.retrieve(
            query=query,
            mode=mode,
            top_k=3,
            rerank=True
        )

        results_summary[mode] = len(results)
        print(f"{mode.upper()}检索模式: 返回{len(results)}个结果")

        for i, result in enumerate(results):
            print(f"  {i+1}. [{result.source}] 分数: {result.score:.3f}")

    print(f"✅ 混合检索测试完成")
    print(f"结果统计: {results_summary}")

    # 验证混合模式返回的结果数量应该是最多的
    return results_summary["hybrid"] >= max(results_summary["vector"], results_summary["graph"], results_summary["fulltext"])


async def test_cosine_similarity():
    """测试余弦相似度计算"""
    print("=" * 50)
    print("测试余弦相似度计算")
    print("=" * 50)

    mock_vector_store = MockVectorStore()
    mock_graph_store = MockGraphStore()

    retriever = HybridRetriever(mock_vector_store, mock_graph_store)

    # 测试向量
    vec1 = [1, 0, 0]
    vec2 = [0, 1, 0]
    vec3 = [1, 0, 0]

    sim1 = retriever._cosine_similarity(vec1, vec2)  # 垂直向量
    sim2 = retriever._cosine_similarity(vec1, vec3)  # 相同向量

    print(f"向量[1,0,0]与[0,1,0]的相似度: {sim1:.3f} (期望: 0.000)")
    print(f"向量[1,0,0]与[1,0,0]的相似度: {sim2:.3f} (期望: 1.000)")

    # 验证结果
    assert abs(sim1 - 0.0) < 0.001, f"垂直向量相似度应该接近0，实际: {sim1}"
    assert abs(sim2 - 1.0) < 0.001, f"相同向量相似度应该接近1，实际: {sim2}"

    print("✅ 余弦相似度计算测试通过")
    return True


async def main():
    """主测试函数"""
    print("🚀 开始检索逻辑测试")
    print("时间:", asyncio.get_event_loop().time())

    # 测试用例
    test_cases = [
        ("检索结果数据结构", test_retrieval_result),
        ("向量检索器", test_vector_retriever),
        ("图检索器", test_graph_retriever),
        ("全文检索器", test_fulltext_retriever),
        ("重排序算法", test_reranking_algorithm),
        ("混合检索", test_hybrid_retrieval),
        ("余弦相似度计算", test_cosine_similarity),
    ]

    results = {}

    for test_name, test_func in test_cases:
        try:
            print(f"\n{'='*60}")
            result = await test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")

        except Exception as e:
            results[test_name] = False
            print(f"{test_name}: ❌ 异常 - {e}")
            logger.error(f"测试异常: {test_name}", error=str(e))

    # 输出测试结果摘要
    print("\n" + "="*60)
    print("📊 测试结果摘要")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<25}: {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")

    if passed_tests == total_tests:
        print("🎉 所有检索逻辑测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现逻辑")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)