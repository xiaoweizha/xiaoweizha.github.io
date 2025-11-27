#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from src.core.graph_store import GraphStore
from src.utils.config import get_config

async def view_graph_data():
    """查看知识图谱数据"""
    print("🕸️ 知识图谱数据查看")
    print("=" * 60)

    try:
        # 初始化图存储
        graph_store = GraphStore("neo4j")

        await graph_store.initialize()
        print("✅ 成功连接到Neo4j数据库\n")

        # 获取图谱统计信息
        stats = await get_graph_statistics(graph_store)
        print_graph_statistics(stats)

        # 获取实体列表
        entities = await get_entities(graph_store, limit=20)
        print_entities(entities)

        # 获取关系列表
        relationships = await get_relationships(graph_store, limit=15)
        print_relationships(relationships)

        # 获取实体度数排行
        top_entities = await get_top_entities_by_degree(graph_store, limit=10)
        print_top_entities(top_entities)

        await graph_store.close()

    except Exception as e:
        print(f"❌ 连接图数据库失败: {e}")

async def get_graph_statistics(graph_store):
    """获取图谱统计信息"""
    try:
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->()
        RETURN
            count(DISTINCT n) as node_count,
            count(r) as relationship_count,
            count(DISTINCT labels(n)) as label_count
        """
        result = await graph_store.execute_query(query)
        return result[0] if result else {}
    except:
        return {}

async def get_entities(graph_store, limit=20):
    """获取实体列表"""
    try:
        query = f"""
        MATCH (n)
        RETURN
            labels(n)[0] as entity_type,
            n.name as entity_name,
            id(n) as node_id,
            size((n)--()) as degree
        ORDER BY degree DESC
        LIMIT {limit}
        """
        return await graph_store.execute_query(query)
    except:
        return []

async def get_relationships(graph_store, limit=15):
    """获取关系列表"""
    try:
        query = f"""
        MATCH (a)-[r]->(b)
        RETURN
            a.name as source,
            type(r) as relationship_type,
            b.name as target,
            r.weight as weight
        ORDER BY r.weight DESC
        LIMIT {limit}
        """
        return await graph_store.execute_query(query)
    except:
        return []

async def get_top_entities_by_degree(graph_store, limit=10):
    """获取度数最高的实体"""
    try:
        query = f"""
        MATCH (n)
        RETURN
            n.name as entity_name,
            labels(n)[0] as entity_type,
            size((n)--()) as degree,
            size((n)-->()) as out_degree,
            size((n)<--()) as in_degree
        ORDER BY degree DESC
        LIMIT {limit}
        """
        return await graph_store.execute_query(query)
    except:
        return []

def print_graph_statistics(stats):
    """打印图谱统计信息"""
    if not stats:
        print("❌ 无法获取图谱统计信息\n")
        return

    print("📊 图谱统计信息:")
    print(f"   🔵 节点数量: {stats.get('node_count', 0)}")
    print(f"   🔗 关系数量: {stats.get('relationship_count', 0)}")
    print(f"   🏷️  标签类型: {stats.get('label_count', 0)}")
    print()

def print_entities(entities):
    """打印实体列表"""
    if not entities:
        print("❌ 未找到实体数据\n")
        return

    print("🎯 实体列表 (按度数排序):")
    print("-" * 60)
    for i, entity in enumerate(entities, 1):
        entity_type = entity.get('entity_type', 'Unknown')
        entity_name = entity.get('entity_name', 'Unknown')
        degree = entity.get('degree', 0)
        print(f"{i:2d}. 📝 {entity_name} ({entity_type}) - 连接数: {degree}")
    print()

def print_relationships(relationships):
    """打印关系列表"""
    if not relationships:
        print("❌ 未找到关系数据\n")
        return

    print("🔗 关系列表 (按权重排序):")
    print("-" * 80)
    for i, rel in enumerate(relationships, 1):
        source = rel.get('source', 'Unknown')
        rel_type = rel.get('relationship_type', 'Unknown')
        target = rel.get('target', 'Unknown')
        weight = rel.get('weight', 0)
        print(f"{i:2d}. {source} --[{rel_type}]-> {target} (权重: {weight})")
    print()

def print_top_entities(top_entities):
    """打印度数最高的实体"""
    if not top_entities:
        print("❌ 未找到实体度数数据\n")
        return

    print("🏆 核心实体排行榜:")
    print("-" * 70)
    print("    实体名称           类型        总度数  出度  入度")
    print("-" * 70)

    for i, entity in enumerate(top_entities, 1):
        name = entity.get('entity_name', 'Unknown')[:15]
        entity_type = entity.get('entity_type', 'Unknown')[:8]
        degree = entity.get('degree', 0)
        out_degree = entity.get('out_degree', 0)
        in_degree = entity.get('in_degree', 0)

        print(f"{i:2d}. {name:<15} {entity_type:<8} {degree:>6}  {out_degree:>4}  {in_degree:>4}")
    print()

async def search_entity(graph_store, entity_name):
    """搜索特定实体及其关系"""
    print(f"🔍 搜索实体: {entity_name}")
    print("-" * 50)

    try:
        # 查找实体信息
        query = """
        MATCH (n)
        WHERE n.name CONTAINS $entity_name
        RETURN
            n.name as name,
            labels(n)[0] as type,
            size((n)--()) as degree
        LIMIT 5
        """
        entities = await graph_store.execute_query(query, {"entity_name": entity_name})

        if not entities:
            print(f"❌ 未找到包含 '{entity_name}' 的实体")
            return

        for entity in entities:
            name = entity['name']
            entity_type = entity['type']
            degree = entity['degree']

            print(f"📝 实体: {name} ({entity_type}) - 连接数: {degree}")

            # 查找该实体的关系
            rel_query = """
            MATCH (n {name: $name})-[r]-(m)
            RETURN
                type(r) as rel_type,
                m.name as connected_entity,
                labels(m)[0] as connected_type
            LIMIT 10
            """
            relationships = await graph_store.execute_query(rel_query, {"name": name})

            if relationships:
                print("   关系:")
                for rel in relationships:
                    rel_type = rel['rel_type']
                    connected = rel['connected_entity']
                    conn_type = rel['connected_type']
                    print(f"     🔗 {rel_type} -> {connected} ({conn_type})")
            print()

    except Exception as e:
        print(f"❌ 搜索失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 搜索特定实体
        entity_name = sys.argv[1]
        asyncio.run(view_graph_data())
        # 然后搜索
        async def search_wrapper():
            graph_store = GraphStore("neo4j")
            await graph_store.initialize()
            await search_entity(graph_store, entity_name)
            await graph_store.close()
        asyncio.run(search_wrapper())
    else:
        # 显示图谱概览
        asyncio.run(view_graph_data())
        print("💡 提示：使用 'python3 view_graph.py <实体名>' 搜索特定实体")