#!/usr/bin/env python3
"""
集成检索功能测试

测试向量检索、图检索和混合检索的完整功能。
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.vector_store import VectorStore
from src.core.graph_store import GraphStore
from src.core.retriever import HybridRetriever
from src.core.embeddings import get_embedding_provider
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class MockDocumentChunk:
    """模拟文档块用于测试"""

    def __init__(self, document_id: str, chunk_index: int, content: str, metadata: Dict[str, Any] = None):
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.metadata = metadata or {}
        self.embedding = None
        self.start_pos = 0
        self.end_pos = len(content)


async def test_vector_store():
    """测试向量存储功能"""
    print("=" * 50)
    print("测试向量存储功能")
    print("=" * 50)

    try:
        # 初始化向量存储
        vector_store = VectorStore(store_type="qdrant")
        success = await vector_store.initialize()

        if not success:
            print("❌ 向量存储初始化失败，可能Qdrant服务未启动")
            return False

        print("✅ 向量存储初始化成功")

        # 测试健康检查
        health = await vector_store.health_check()
        print(f"健康状态: {health}")

        # 创建测试文档块
        test_chunks = [
            MockDocumentChunk(
                "doc1", 0,
                "RAG (检索增强生成) 是一种结合了信息检索和文本生成的人工智能技术。它通过从大型知识库中检索相关信息来增强语言模型的生成能力。",
                {"title": "RAG技术简介", "category": "AI"}
            ),
            MockDocumentChunk(
                "doc1", 1,
                "知识图谱是一种用图结构来表示知识的技术，它能够有效地组织和表示实体之间的复杂关系。在RAG系统中，知识图谱提供了结构化的知识表示。",
                {"title": "知识图谱在RAG中的应用", "category": "AI"}
            ),
            MockDocumentChunk(
                "doc2", 0,
                "向量检索是现代搜索系统的核心技术之一。通过将文档和查询转换为高维向量，我们可以计算语义相似度来找到最相关的内容。",
                {"title": "向量检索技术", "category": "Search"}
            )
        ]

        # 测试添加文档块
        result = await vector_store.add_chunks(test_chunks)
        print(f"添加文档块结果: {result}")

        # 测试向量搜索
        embedding_provider = get_embedding_provider()
        query = "什么是RAG技术？"
        query_vector = await embedding_provider.embed_text(query)

        search_results = await vector_store.search_vectors(query_vector, top_k=5)
        print(f"\n向量搜索结果 (查询: '{query}'):")
        for i, result in enumerate(search_results):
            print(f"  {i+1}. 分数: {result['score']:.3f}")
            print(f"     内容: {result['metadata'].get('content', '')[:100]}...")
            print()

        # 获取统计信息
        stats = await vector_store.get_statistics()
        print(f"向量存储统计: {stats}")

        return True

    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        logger.error("向量存储测试异常", error=str(e))
        return False


async def test_graph_store():
    """测试图存储功能"""
    print("=" * 50)
    print("测试图存储功能")
    print("=" * 50)

    try:
        # 初始化图存储
        graph_store = GraphStore(store_type="neo4j")
        success = await graph_store.initialize()

        if not success:
            print("❌ 图存储初始化失败，可能Neo4j服务未启动")
            return False

        print("✅ 图存储初始化成功")

        # 测试健康检查
        health = await graph_store.health_check()
        print(f"健康状态: {health}")

        # 创建测试文档块
        test_chunks = [
            MockDocumentChunk(
                "doc1", 0,
                "RAG技术是现代AI系统中的重要组成部分，它结合了检索和生成两个核心能力。",
                {"title": "RAG技术概述", "category": "AI"}
            ),
            MockDocumentChunk(
                "doc1", 1,
                "知识图谱在RAG系统中发挥着重要作用，提供结构化的知识表示和查询能力。",
                {"title": "知识图谱应用", "category": "AI"}
            )
        ]

        # 测试构建知识图谱
        result = await graph_store.build_graph_from_chunks(test_chunks)
        print(f"知识图谱构建结果: {result}")

        # 测试查询实体
        entities = await graph_store.query_entities(limit=5)
        print(f"\n图中的实体 (前5个):")
        for entity in entities:
            print(f"  - {entity['id']} ({entity['type']})")

        # 测试查询关系
        relations = await graph_store.query_relations(limit=5)
        print(f"\n图中的关系 (前5个):")
        for relation in relations:
            print(f"  - {relation['from_entity']} --[{relation['type']}]--> {relation['to_entity']}")

        # 获取统计信息
        stats = await graph_store.get_statistics()
        print(f"\n图存储统计: {stats}")

        return True

    except Exception as e:
        print(f"❌ 图存储测试失败: {e}")
        logger.error("图存储测试异常", error=str(e))
        return False


async def test_hybrid_retriever():
    """测试混合检索器功能"""
    print("=" * 50)
    print("测试混合检索器功能")
    print("=" * 50)

    try:
        # 初始化存储组件
        vector_store = VectorStore(store_type="qdrant")
        graph_store = GraphStore(store_type="neo4j")

        # 尝试初始化，如果失败则使用模拟模式
        vector_success = await vector_store.initialize()
        graph_success = await graph_store.initialize()

        if not vector_success:
            print("⚠️  向量存储不可用，将使用模拟结果")
        if not graph_success:
            print("⚠️  图存储不可用，将使用模拟结果")

        # 初始化混合检索器
        retriever = HybridRetriever(vector_store, graph_store)
        await retriever.initialize()
        print("✅ 混合检索器初始化成功")

        # 测试不同的检索模式
        test_queries = [
            "RAG技术的工作原理是什么？",
            "知识图谱如何与向量检索结合？",
            "人工智能中的检索增强生成技术"
        ]

        retrieval_modes = ["vector", "graph", "fulltext", "hybrid"]

        for query in test_queries:
            print(f"\n查询: '{query}'")
            print("-" * 40)

            for mode in retrieval_modes:
                try:
                    results = await retriever.retrieve(
                        query=query,
                        mode=mode,
                        top_k=3,
                        rerank=True
                    )

                    print(f"\n{mode.upper()}检索结果:")
                    if results:
                        for i, result in enumerate(results):
                            print(f"  {i+1}. [{result.source}] 分数: {result.score:.3f}")
                            print(f"     内容: {result.content[:80]}...")
                    else:
                        print("  无结果")

                except Exception as e:
                    print(f"  ❌ {mode}检索失败: {e}")

            print("\n" + "="*50)

        # 测试健康检查
        health = await retriever.health_check()
        print(f"\n检索器健康状态: {health}")

        # 获取统计信息
        stats = await retriever.get_statistics()
        print(f"检索器统计信息: {stats}")

        # 清理资源
        await retriever.close()

        return True

    except Exception as e:
        print(f"❌ 混合检索器测试失败: {e}")
        logger.error("混合检索器测试异常", error=str(e))
        return False


async def main():
    """主测试函数"""
    print("🚀 开始集成检索功能测试")
    print("时间:", asyncio.get_event_loop().time())

    # 测试结果统计
    test_results = {
        "vector_store": False,
        "graph_store": False,
        "hybrid_retriever": False
    }

    try:
        # 测试向量存储
        test_results["vector_store"] = await test_vector_store()

        # 测试图存储
        test_results["graph_store"] = await test_graph_store()

        # 测试混合检索器
        test_results["hybrid_retriever"] = await test_hybrid_retriever()

    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        logger.error("测试异常", error=str(e))

    # 输出测试结果摘要
    print("\n" + "="*60)
    print("📊 测试结果摘要")
    print("="*60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<20}: {status}")

    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")

    if passed_tests == total_tests:
        print("🎉 所有核心检索功能测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查依赖服务状态")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)