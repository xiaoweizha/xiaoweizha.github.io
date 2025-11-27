#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from src.core.graph_store import GraphStore

async def view_simple_graph():
    """简单查看图谱数据"""
    print("🕸️ 知识图谱简单查看")
    print("=" * 50)

    try:
        # 初始化图存储
        graph_store = GraphStore("neo4j")
        success = await graph_store.initialize()

        if not success:
            print("❌ 无法连接到Neo4j数据库")
            return

        print("✅ 成功连接到Neo4j数据库\n")

        # 查询实体
        print("📋 查询实体:")
        entities = await graph_store.query_entities(limit=10)
        if entities:
            print(f"找到 {len(entities)} 个实体:")
            for i, entity in enumerate(entities, 1):
                print(f"  {i}. {entity}")
        else:
            print("  未找到实体数据")

        print()

        # 查询关系
        print("🔗 查询关系:")
        relations = await graph_store.query_relations(limit=10)
        if relations:
            print(f"找到 {len(relations)} 个关系:")
            for i, relation in enumerate(relations, 1):
                print(f"  {i}. {relation}")
        else:
            print("  未找到关系数据")

        # 不需要手动关闭，让系统自动处理

    except Exception as e:
        print(f"❌ 查看图谱失败: {e}")

if __name__ == "__main__":
    asyncio.run(view_simple_graph())