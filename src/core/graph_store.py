"""
图数据库存储模块

知识图谱数据的存储和查询。
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import json
import asyncio

from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class GraphStoreBase(ABC):
    """图存储基类"""

    @abstractmethod
    async def add_entity(self, entity: Dict[str, Any]) -> str:
        """添加实体"""
        pass

    @abstractmethod
    async def add_relation(self, relation: Dict[str, Any]) -> str:
        """添加关系"""
        pass

    @abstractmethod
    async def query_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询实体"""
        pass

    @abstractmethod
    async def query_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询关系"""
        pass

    @abstractmethod
    async def find_path(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """查找路径"""
        pass


class Neo4jGraphStore(GraphStoreBase):
    """Neo4j图存储实现"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config().database
        self.driver = None

    async def initialize(self):
        """初始化Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            import asyncio

            # 初始化Neo4j驱动
            neo4j_uri = getattr(self.config, 'neo4j_uri', 'bolt://localhost:7687')
            neo4j_user = getattr(self.config, 'neo4j_username', 'neo4j')
            neo4j_password = getattr(self.config, 'neo4j_password', 'password')

            self.driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )

            # 测试连接
            def _test_connection():
                with self.driver.session() as session:
                    result = session.run("RETURN 1 as num")
                    return result.single()["num"] == 1

            # 在线程池中执行同步操作
            success = await asyncio.to_thread(_test_connection)

            if success:
                # 创建索引以提升查询性能
                await self._create_indexes()

            logger.info("Neo4j图存储初始化成功")
            return True

        except Exception as e:
            logger.error("Neo4j初始化失败", error=str(e))
            return False

    async def _create_indexes(self):
        """创建必要的索引"""
        try:
            def _create_indexes_sync():
                with self.driver.session() as session:
                    # 为实体ID创建索引
                    session.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)")
                    # 为文档ID创建索引
                    session.run("CREATE INDEX document_id_index IF NOT EXISTS FOR (d:Document) ON (d.document_id)")
                    # 为主题名称创建索引
                    session.run("CREATE INDEX topic_name_index IF NOT EXISTS FOR (t:Topic) ON (t.name)")

            await asyncio.to_thread(_create_indexes_sync)
            logger.info("Neo4j索引创建完成")

        except Exception as e:
            logger.warning("创建Neo4j索引时出现警告", error=str(e))

    async def add_entity(self, entity: Dict[str, Any]) -> str:
        """添加实体到Neo4j"""
        try:
            if not self.driver:
                raise RuntimeError("Neo4j驱动未初始化")

            entity_id = entity.get("id", f"entity_{hash(str(entity))}")
            entity_type = entity.get("type", "Entity")
            properties = entity.get("properties", {})

            # 准备属性，确保所有值都是可序列化的
            safe_properties = {"id": entity_id}
            for key, value in properties.items():
                if isinstance(value, (str, int, float, bool)):
                    safe_properties[key] = value
                else:
                    safe_properties[key] = str(value)

            def _add_entity_sync():
                with self.driver.session() as session:
                    # 使用MERGE确保实体唯一性
                    cypher = f"""
                    MERGE (e:{entity_type} {{id: $id}})
                    SET e += $properties
                    RETURN e.id as entity_id
                    """
                    result = session.run(cypher, id=entity_id, properties=safe_properties)
                    return result.single()["entity_id"]

            # 在线程池中执行
            result_id = await asyncio.to_thread(_add_entity_sync)

            logger.debug(f"添加实体成功: {entity_id}")
            return result_id

        except Exception as e:
            logger.error("添加实体失败", error=str(e))
            raise

    async def add_relation(self, relation: Dict[str, Any]) -> str:
        """添加关系到Neo4j"""
        try:
            if not self.driver:
                raise RuntimeError("Neo4j驱动未初始化")

            from_entity = relation.get("from_entity")
            to_entity = relation.get("to_entity")
            relation_type = relation.get("type", "RELATED_TO").upper()
            properties = relation.get("properties", {})

            if not from_entity or not to_entity:
                raise ValueError("from_entity和to_entity都必须提供")

            # 准备属性
            safe_properties = {}
            for key, value in properties.items():
                if isinstance(value, (str, int, float, bool)):
                    safe_properties[key] = value
                else:
                    safe_properties[key] = str(value)

            def _add_relation_sync():
                with self.driver.session() as session:
                    # 创建关系，确保两个实体都存在
                    cypher = f"""
                    MATCH (a {{id: $from_entity}})
                    MATCH (b {{id: $to_entity}})
                    MERGE (a)-[r:{relation_type}]->(b)
                    SET r += $properties
                    RETURN id(r) as relation_id
                    """
                    result = session.run(
                        cypher,
                        from_entity=from_entity,
                        to_entity=to_entity,
                        properties=safe_properties
                    )
                    record = result.single()
                    return record["relation_id"] if record else None

            # 在线程池中执行
            relation_id = await asyncio.to_thread(_add_relation_sync)

            if relation_id is None:
                logger.warning(f"关系创建可能失败: {from_entity} -> {to_entity}")
                return f"{from_entity}_{relation_type}_{to_entity}"

            logger.debug(f"添加关系成功: {from_entity} -> {to_entity}")
            return str(relation_id)

        except Exception as e:
            logger.error("添加关系失败", error=str(e))
            raise

    async def query_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询实体"""
        try:
            if not self.driver:
                raise RuntimeError("Neo4j驱动未初始化")

            def _query_entities_sync():
                with self.driver.session() as session:
                    # 构建Cypher查询
                    cypher_parts = []
                    params = {"limit": limit}

                    if entity_type:
                        cypher_parts.append(f"MATCH (e:{entity_type})")
                    else:
                        cypher_parts.append("MATCH (e)")

                    # 添加过滤条件
                    where_conditions = []
                    if filters:
                        for key, value in filters.items():
                            if key != "id":  # id通常需要特殊处理
                                param_name = f"filter_{key}"
                                where_conditions.append(f"e.{key} = ${param_name}")
                                params[param_name] = value

                    if where_conditions:
                        cypher_parts.append("WHERE " + " AND ".join(where_conditions))

                    cypher_parts.append("RETURN e, labels(e) as labels")
                    cypher_parts.append("LIMIT $limit")

                    cypher = " ".join(cypher_parts)

                    result = session.run(cypher, **params)
                    entities = []

                    for record in result:
                        node = record["e"]
                        labels = record["labels"]

                        entity = {
                            "id": node.get("id", ""),
                            "type": labels[0] if labels else "Entity",
                            "labels": labels,
                            "properties": dict(node)
                        }
                        entities.append(entity)

                    return entities

            # 在线程池中执行
            results = await asyncio.to_thread(_query_entities_sync)

            logger.debug(f"查询实体完成，找到{len(results)}个结果")
            return results

        except Exception as e:
            logger.error("查询实体失败", error=str(e))
            return []

    async def query_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询关系"""
        try:
            if not self.driver:
                raise RuntimeError("Neo4j驱动未初始化")

            def _query_relations_sync():
                with self.driver.session() as session:
                    # 构建Cypher查询
                    cypher_parts = []
                    params = {"limit": limit}

                    # 构建匹配模式
                    if from_entity and to_entity:
                        # 查询特定两个实体之间的关系
                        cypher_parts.append("MATCH (a {id: $from_entity})-[r]->(b {id: $to_entity})")
                        params["from_entity"] = from_entity
                        params["to_entity"] = to_entity
                    elif from_entity:
                        # 查询从特定实体出发的关系
                        cypher_parts.append("MATCH (a {id: $from_entity})-[r]->(b)")
                        params["from_entity"] = from_entity
                    elif to_entity:
                        # 查询指向特定实体的关系
                        cypher_parts.append("MATCH (a)-[r]->(b {id: $to_entity})")
                        params["to_entity"] = to_entity
                    else:
                        # 查询所有关系
                        cypher_parts.append("MATCH (a)-[r]->(b)")

                    # 添加关系类型过滤
                    if relation_type:
                        cypher_parts[0] = cypher_parts[0].replace("-[r]->", f"-[r:{relation_type.upper()}]->")

                    cypher_parts.append("RETURN a.id as from_entity, b.id as to_entity, type(r) as relation_type, properties(r) as properties, id(r) as relation_id")
                    cypher_parts.append("LIMIT $limit")

                    cypher = " ".join(cypher_parts)

                    result = session.run(cypher, **params)
                    relations = []

                    for record in result:
                        relation = {
                            "id": str(record["relation_id"]),
                            "from_entity": record["from_entity"],
                            "to_entity": record["to_entity"],
                            "type": record["relation_type"],
                            "properties": record["properties"] or {}
                        }
                        relations.append(relation)

                    return relations

            # 在线程池中执行
            results = await asyncio.to_thread(_query_relations_sync)

            logger.debug(f"查询关系完成，找到{len(results)}个结果")
            return results

        except Exception as e:
            logger.error("查询关系失败", error=str(e))
            return []

    async def find_path(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """查找实体间路径"""
        try:
            if not self.driver:
                raise RuntimeError("Neo4j驱动未初始化")

            def _find_path_sync():
                with self.driver.session() as session:
                    # 使用Neo4j的最短路径算法
                    cypher = f"""
                    MATCH path = shortestPath(
                        (start {{id: $start_entity}})-[*1..{max_depth}]-(end {{id: $end_entity}})
                    )
                    WHERE start.id <> end.id
                    RETURN path
                    LIMIT 10
                    """

                    result = session.run(cypher, start_entity=start_entity, end_entity=end_entity)
                    paths = []

                    for record in result:
                        path_data = record["path"]
                        path_elements = []

                        # 解析路径中的节点和关系
                        nodes = path_data.nodes
                        relationships = path_data.relationships

                        for i, node in enumerate(nodes):
                            # 添加节点
                            element = {
                                "type": "entity",
                                "id": node.get("id", ""),
                                "labels": list(node.labels),
                                "properties": dict(node)
                            }
                            path_elements.append(element)

                            # 添加关系（如果不是最后一个节点）
                            if i < len(relationships):
                                rel = relationships[i]
                                rel_element = {
                                    "type": "relation",
                                    "relation_type": rel.type,
                                    "properties": dict(rel)
                                }
                                path_elements.append(rel_element)

                        if path_elements:
                            paths.append(path_elements)

                    return paths

            # 在线程池中执行
            results = await asyncio.to_thread(_find_path_sync)

            logger.debug(f"路径查找完成，找到{len(results)}条路径")
            return results

        except Exception as e:
            logger.error("路径查找失败", error=str(e))
            return []


class GraphStore:
    """图存储统一接口"""

    def __init__(self, store_type: str = "neo4j"):
        self.store_type = store_type
        self.store = None

    async def initialize(self):
        """初始化图存储"""
        try:
            if self.store_type == "neo4j":
                self.store = Neo4jGraphStore()
            else:
                raise ValueError(f"不支持的图存储类型: {self.store_type}")

            success = await self.store.initialize()
            if success:
                logger.info(f"图存储初始化成功: {self.store_type}")
            else:
                logger.error(f"图存储初始化失败: {self.store_type}")

            return success

        except Exception as e:
            logger.error("图存储初始化异常", error=str(e))
            return False

    async def add_entity(self, entity: Dict[str, Any]) -> str:
        """添加实体"""
        if not self.store:
            raise RuntimeError("图存储未初始化")
        return await self.store.add_entity(entity)

    async def add_relation(self, relation: Dict[str, Any]) -> str:
        """添加关系"""
        if not self.store:
            raise RuntimeError("图存储未初始化")
        return await self.store.add_relation(relation)

    async def query_entities(
        self,
        entity_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询实体"""
        if not self.store:
            raise RuntimeError("图存储未初始化")
        return await self.store.query_entities(entity_type, filters, limit)

    async def query_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询关系"""
        if not self.store:
            raise RuntimeError("图存储未初始化")
        return await self.store.query_relations(from_entity, to_entity, relation_type, limit)

    async def find_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """查找相关实体"""
        try:
            # 查找直接关系
            relations = await self.query_relations(from_entity=entity_id, limit=50)

            related_entities = []
            for relation in relations:
                entity_data = {
                    "entity_id": relation["to_entity"],
                    "relation_type": relation["type"],
                    "weight": relation.get("properties", {}).get("weight", 0.5),
                    "depth": 1
                }
                related_entities.append(entity_data)

            return related_entities

        except Exception as e:
            logger.error("查找相关实体失败", error=str(e))
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        if not self.store:
            return {"status": "未初始化", "entities": 0, "relations": 0}

        try:
            def _get_statistics_sync():
                with self.store.driver.session() as session:
                    # 统计实体数量
                    entity_result = session.run("MATCH (n) RETURN count(n) as entity_count")
                    entity_count = entity_result.single()["entity_count"]

                    # 统计关系数量
                    relation_result = session.run("MATCH ()-[r]->() RETURN count(r) as relation_count")
                    relation_count = relation_result.single()["relation_count"]

                    # 统计不同类型的实体
                    type_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                    entity_types = {}
                    for record in type_result:
                        labels = record["labels"]
                        count = record["count"]
                        if labels:
                            entity_types[labels[0]] = count

                    return {
                        "entity_count": entity_count,
                        "relation_count": relation_count,
                        "entity_types": entity_types
                    }

            # 在线程池中执行
            stats = await asyncio.to_thread(_get_statistics_sync)

            return {
                "status": "正常",
                "type": self.store_type,
                "entities": stats["entity_count"],
                "relations": stats["relation_count"],
                "entity_types": stats["entity_types"]
            }

        except Exception as e:
            logger.error("获取图统计失败", error=str(e))
            return {"status": "异常", "error": str(e)}

    async def build_graph_from_chunks(self, chunks) -> Dict[str, Any]:
        """
        从文档块构建知识图谱

        Args:
            chunks: DocumentChunk 列表

        Returns:
            图谱构建结果
        """
        if not self.store:
            raise RuntimeError("图存储未初始化")

        try:
            entities_added = 0
            relations_added = 0

            # 简化的知识图谱构建逻辑
            for chunk in chunks:
                # 从文档块内容中提取实体和关系
                # 这里使用简化的逻辑，实际应该使用NLP技术进行实体识别

                # 创建文档节点
                doc_entity = {
                    "id": f"doc_{chunk.document_id}",
                    "type": "Document",
                    "properties": {
                        "document_id": chunk.document_id,
                        "title": chunk.metadata.get("title", f"文档{chunk.document_id[:8]}"),
                        "created_at": chunk.metadata.get("created_at", "")
                    }
                }

                # 创建块节点
                chunk_entity = {
                    "id": f"chunk_{chunk.document_id}_{chunk.chunk_index}",
                    "type": "DocumentChunk",
                    "properties": {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "content_preview": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                        "content_length": len(chunk.content)
                    }
                }

                # 添加实体
                await self.add_entity(doc_entity)
                await self.add_entity(chunk_entity)
                entities_added += 2

                # 创建文档-块关系
                doc_chunk_relation = {
                    "from_entity": doc_entity["id"],
                    "to_entity": chunk_entity["id"],
                    "type": "CONTAINS_CHUNK",
                    "properties": {
                        "chunk_order": chunk.chunk_index,
                        "weight": 1.0
                    }
                }
                await self.add_relation(doc_chunk_relation)
                relations_added += 1

                # 基于内容的简单主题提取
                content_lower = chunk.content.lower()
                topics = []

                # 简单的关键词匹配
                if "rag" in content_lower or "检索" in content_lower:
                    topics.append("RAG技术")
                if "知识图谱" in content_lower or "图谱" in content_lower:
                    topics.append("知识图谱")
                if "向量" in content_lower or "嵌入" in content_lower:
                    topics.append("向量检索")
                if "ai" in content_lower or "人工智能" in content_lower:
                    topics.append("人工智能")

                # 为每个主题创建节点和关系
                for topic in topics:
                    topic_entity = {
                        "id": f"topic_{topic.replace(' ', '_')}",
                        "type": "Topic",
                        "properties": {
                            "name": topic,
                            "category": "技术概念"
                        }
                    }

                    topic_relation = {
                        "from_entity": chunk_entity["id"],
                        "to_entity": topic_entity["id"],
                        "type": "RELATES_TO",
                        "properties": {
                            "confidence": 0.8,
                            "weight": 0.6
                        }
                    }

                    await self.add_entity(topic_entity)
                    await self.add_relation(topic_relation)
                    entities_added += 1
                    relations_added += 1

            logger.info(
                "知识图谱构建完成",
                chunks_count=len(chunks),
                entities_added=entities_added,
                relations_added=relations_added
            )

            return {
                "success": True,
                "chunks_processed": len(chunks),
                "graph_entities": entities_added,
                "graph_relations": relations_added
            }

        except Exception as e:
            logger.error("知识图谱构建失败", error=str(e))
            # 不抛出异常，返回失败结果
            return {
                "success": False,
                "error": str(e),
                "chunks_processed": len(chunks),
                "graph_entities": 0,
                "graph_relations": 0
            }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.store:
                return {"status": "unhealthy", "reason": "未初始化"}

            # 尝试查询来验证连接
            entities = await self.query_entities(limit=1)
            return {"status": "healthy"}

        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}