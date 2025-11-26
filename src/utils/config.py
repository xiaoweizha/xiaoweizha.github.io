"""
配置管理模块

统一管理系统配置，支持多环境配置和动态更新。
"""

import os
from typing import Any, Dict, Optional, Union
from pathlib import Path
import yaml
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
import structlog

logger = structlog.get_logger(__name__)


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    # MongoDB配置
    mongodb_host: str = Field("localhost", env="MONGODB_HOST")
    mongodb_port: int = Field(27017, env="MONGODB_PORT")
    mongodb_database: str = Field("rag_kb", env="MONGODB_DATABASE")
    mongodb_username: Optional[str] = Field(None, env="MONGODB_USERNAME")
    mongodb_password: Optional[str] = Field(None, env="MONGODB_PASSWORD")

    # Neo4j配置
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_username: str = Field("neo4j", env="NEO4J_USERNAME")
    neo4j_password: Optional[str] = Field(None, env="NEO4J_PASSWORD")
    neo4j_database: str = Field("neo4j", env="NEO4J_DATABASE")

    # Qdrant配置
    qdrant_host: str = Field("localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(6333, env="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    qdrant_collection: str = Field("documents", env="QDRANT_COLLECTION")

    # Redis配置
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")

    # Elasticsearch配置
    elasticsearch_hosts: str = Field("localhost:9200", env="ELASTICSEARCH_HOSTS")
    elasticsearch_username: Optional[str] = Field(None, env="ES_USERNAME")
    elasticsearch_password: Optional[str] = Field(None, env="ES_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class LLMConfig(BaseSettings):
    """LLM配置"""
    # 基础配置
    provider: str = Field("openai", env="LLM_PROVIDER")
    model: str = Field("gpt-4-turbo", env="LLM_MODEL")
    temperature: float = Field(0.1, env="LLM_TEMPERATURE")
    max_tokens: int = Field(4096, env="LLM_MAX_TOKENS")
    timeout: int = Field(60, env="LLM_TIMEOUT")

    # OpenAI配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_api_base: Optional[str] = Field(None, env="OPENAI_API_BASE")

    # Azure OpenAI配置
    azure_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_api_key: Optional[str] = Field(None, env="AZURE_OPENAI_API_KEY")
    azure_api_version: str = Field("2024-02-01", env="AZURE_API_VERSION")

    # 中文LLM配置
    qianfan_access_key: Optional[str] = Field(None, env="QIANFAN_ACCESS_KEY")
    qianfan_secret_key: Optional[str] = Field(None, env="QIANFAN_SECRET_KEY")
    tongyi_api_key: Optional[str] = Field(None, env="TONGYI_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class EmbeddingConfig(BaseSettings):
    """Embedding配置"""
    provider: str = Field("openai", env="EMBEDDING_PROVIDER")
    model: str = Field("text-embedding-3-large", env="EMBEDDING_MODEL")
    dimension: int = Field(1536, env="EMBEDDING_DIMENSION")
    batch_size: int = Field(100, env="EMBEDDING_BATCH_SIZE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class RAGConfig(BaseSettings):
    """RAG配置"""
    retrieval_mode: str = Field("hybrid", env="RAG_RETRIEVAL_MODE")
    top_k: int = Field(10, env="RAG_TOP_K")
    similarity_threshold: float = Field(0.7, env="RAG_SIMILARITY_THRESHOLD")
    rerank_enabled: bool = Field(True, env="RAG_RERANK_ENABLED")
    rerank_top_k: int = Field(5, env="RAG_RERANK_TOP_K")
    chunk_size: int = Field(1000, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="RAG_CHUNK_OVERLAP")
    max_chunks_per_doc: int = Field(1000, env="RAG_MAX_CHUNKS_PER_DOC")
    entity_extraction: bool = Field(True, env="RAG_ENTITY_EXTRACTION")
    relation_extraction: bool = Field(True, env="RAG_RELATION_EXTRACTION")
    context_window: int = Field(4000, env="RAG_CONTEXT_WINDOW")
    max_context_tokens: int = Field(3000, env="RAG_MAX_CONTEXT_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class SecurityConfig(BaseSettings):
    """安全配置"""
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(24, env="JWT_EXPIRE_HOURS")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    cors_origins: str = Field("*", env="CORS_ORIGINS")
    rate_limit_requests: int = Field(60, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field("0.0.0.0", env="SERVER_HOST")
    port: int = Field(8000, env="SERVER_PORT")
    workers: int = Field(4, env="SERVER_WORKERS")
    max_connections: int = Field(1000, env="SERVER_MAX_CONNECTIONS")
    keepalive_timeout: int = Field(30, env="SERVER_KEEPALIVE_TIMEOUT")
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class StorageConfig(BaseSettings):
    """存储配置"""
    # 本地存储
    local_base_path: str = Field("./storage", env="LOCAL_STORAGE_PATH")
    max_file_size: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB

    # MinIO配置
    minio_endpoint: Optional[str] = Field(None, env="MINIO_ENDPOINT")
    minio_access_key: Optional[str] = Field(None, env="MINIO_ACCESS_KEY")
    minio_secret_key: Optional[str] = Field(None, env="MINIO_SECRET_KEY")
    minio_bucket: str = Field("rag-documents", env="MINIO_BUCKET")
    minio_secure: bool = Field(False, env="MINIO_SECURE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class MonitoringConfig(BaseSettings):
    """监控配置"""
    # Prometheus
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(9090, env="PROMETHEUS_PORT")

    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_file_path: str = Field("./logs/app.log", env="LOG_FILE_PATH")

    # Sentry
    sentry_enabled: bool = Field(False, env="SENTRY_ENABLED")
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class Config(BaseSettings):
    """主配置类"""
    # 系统基础信息
    system_name: str = Field("企业RAG知识库", env="SYSTEM_NAME")
    system_version: str = Field("1.0.0", env="SYSTEM_VERSION")
    timezone: str = Field("Asia/Shanghai", env="TIMEZONE")
    language: str = Field("zh-CN", env="LANGUAGE")

    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    rag: RAGConfig = RAGConfig()
    security: SecurityConfig = SecurityConfig()
    server: ServerConfig = ServerConfig()
    storage: StorageConfig = StorageConfig()
    monitoring: MonitoringConfig = MonitoringConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, yaml_path: Union[str, Path]) -> "Config":
        """
        从YAML文件加载配置

        Args:
            yaml_path: YAML配置文件路径

        Returns:
            配置实例
        """
        try:
            yaml_path = Path(yaml_path)
            if not yaml_path.exists():
                logger.warning(f"配置文件不存在: {yaml_path}")
                return cls()

            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)

            # 将嵌套字典转换为环境变量格式
            env_vars = cls._flatten_dict(yaml_data)

            # 临时设置环境变量
            original_env = {}
            for key, value in env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = str(value)

            try:
                config = cls()
            finally:
                # 恢复原始环境变量
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

            logger.info(f"从YAML文件加载配置成功: {yaml_path}")
            return config

        except Exception as e:
            logger.error(f"加载YAML配置失败: {e}")
            return cls()

    @staticmethod
    def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """
        扁平化字典，将嵌套字典转换为单层字典

        Args:
            d: 要扁平化的字典
            parent_key: 父键名
            sep: 分隔符

        Returns:
            扁平化后的字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(Config._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        从字典更新配置

        Args:
            updates: 更新的配置字典
        """
        try:
            for key, value in updates.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    # 尝试更新子配置
                    parts = key.split('.')
                    if len(parts) == 2:
                        section, attr = parts
                        if hasattr(self, section):
                            section_obj = getattr(self, section)
                            if hasattr(section_obj, attr):
                                setattr(section_obj, attr, value)

            logger.info("配置更新成功")

        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典

        Returns:
            配置字典
        """
        return {
            "system": {
                "name": self.system_name,
                "version": self.system_version,
                "timezone": self.timezone,
                "language": self.language
            },
            "database": self.database.dict(),
            "llm": self.llm.dict(),
            "embedding": self.embedding.dict(),
            "rag": self.rag.dict(),
            "security": {
                **self.security.dict(),
                "jwt_secret": "***",  # 隐藏敏感信息
                "encryption_key": "***"
            },
            "server": self.server.dict(),
            "storage": {
                **self.storage.dict(),
                "minio_access_key": "***" if self.storage.minio_access_key else None,
                "minio_secret_key": "***" if self.storage.minio_secret_key else None
            },
            "monitoring": self.monitoring.dict()
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置

        Returns:
            验证结果
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # 验证必需的配置项
            if not self.security.jwt_secret:
                validation_result["errors"].append("JWT密钥不能为空")

            if not self.security.encryption_key:
                validation_result["errors"].append("加密密钥不能为空")

            # 验证LLM配置
            if self.llm.provider == "openai" and not self.llm.openai_api_key:
                validation_result["warnings"].append("OpenAI API密钥未配置")

            # 验证数据库连接信息
            if self.database.mongodb_username and not self.database.mongodb_password:
                validation_result["warnings"].append("MongoDB密码未配置")

            if self.database.neo4j_password is None:
                validation_result["warnings"].append("Neo4j密码未配置")

            # 检查存储路径
            storage_path = Path(self.storage.local_base_path)
            if not storage_path.exists():
                try:
                    storage_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    validation_result["errors"].append(f"无法创建存储目录: {e}")

            validation_result["is_valid"] = len(validation_result["errors"]) == 0

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"配置验证失败: {e}")

        return validation_result


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例

    Returns:
        配置实例
    """
    global _config
    if _config is None:
        # 尝试从YAML文件加载配置
        yaml_config_path = Path("config/config.yaml")
        if yaml_config_path.exists():
            _config = Config.load_from_yaml(yaml_config_path)
        else:
            _config = Config()

        # 验证配置
        validation = _config.validate_config()
        if not validation["is_valid"]:
            logger.warning("配置验证失败", errors=validation["errors"])
        if validation["warnings"]:
            logger.warning("配置警告", warnings=validation["warnings"])

    return _config


def reload_config() -> Config:
    """
    重新加载配置

    Returns:
        新的配置实例
    """
    global _config
    _config = None
    return get_config()


def update_config(updates: Dict[str, Any]) -> None:
    """
    更新配置

    Args:
        updates: 更新的配置
    """
    config = get_config()
    config.update_from_dict(updates)