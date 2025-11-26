"""
数据模型Schema定义

定义系统中所有数据结构的Pydantic模型。
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, validator
import uuid


class DocumentStatus(str, Enum):
    """文档状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class QueryMode(str, Enum):
    """查询模式"""
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"
    NAIVE = "naive"
    MIX = "mix"


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    KNOWLEDGE_MANAGER = "knowledge_manager"
    KNOWLEDGE_WORKER = "knowledge_worker"
    VIEWER = "viewer"


# ==================== 基础数据模型 ====================

class BaseSchema(BaseModel):
    """基础Schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Document(BaseSchema):
    """文档模型"""
    filename: str = Field(..., description="文件名")
    title: Optional[str] = Field(None, description="文档标题")
    content: Optional[Union[str, bytes]] = Field(None, description="文档内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    status: DocumentStatus = Field(DocumentStatus.PENDING, description="处理状态")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    author: Optional[str] = Field(None, description="作者")
    source: Optional[str] = Field(None, description="来源")
    language: Optional[str] = Field("zh-cn", description="语言")
    tags: List[str] = Field(default_factory=list, description="标签")
    knowledge_base_id: Optional[str] = Field(None, description="所属知识库ID")
    user_id: Optional[str] = Field(None, description="上传用户ID")

    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('文件名不能为空')
        return v.strip()


class DocumentChunk(BaseSchema):
    """文档块模型"""
    document_id: str = Field(..., description="所属文档ID")
    content: str = Field(..., description="块内容")
    chunk_index: int = Field(..., description="块索引")
    start_pos: Optional[int] = Field(None, description="在原文档中的起始位置")
    end_pos: Optional[int] = Field(None, description="在原文档中的结束位置")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('块内容不能为空')
        if len(v) > 10000:  # 限制块大小
            raise ValueError('块内容过长')
        return v.strip()


class Entity(BaseSchema):
    """实体模型"""
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(None, description="实体描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实体属性")
    source_chunks: List[str] = Field(default_factory=list, description="来源块ID列表")
    frequency: int = Field(1, description="出现频次")
    confidence: float = Field(1.0, description="置信度")


class Relation(BaseSchema):
    """关系模型"""
    source: str = Field(..., description="源实体ID")
    target: str = Field(..., description="目标实体ID")
    relation: str = Field(..., description="关系类型")
    description: Optional[str] = Field(None, description="关系描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    source_chunks: List[str] = Field(default_factory=list, description="来源块ID列表")
    weight: float = Field(1.0, description="关系权重")
    confidence: float = Field(1.0, description="置信度")


# ==================== 检索和生成模型 ====================

class RetrievalResult(BaseModel):
    """检索结果模型"""
    query: str = Field(..., description="查询文本")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="检索到的文档块")
    entities: List[Entity] = Field(default_factory=list, description="相关实体")
    relations: List[Relation] = Field(default_factory=list, description="相关关系")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="来源信息")
    scores: List[float] = Field(default_factory=list, description="相似度分数")
    retrieval_time: float = Field(0.0, description="检索耗时(秒)")
    mode: QueryMode = Field(QueryMode.HYBRID, description="检索模式")


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., min_length=1, max_length=1000, description="查询文本")
    mode: QueryMode = Field(QueryMode.HYBRID, description="检索模式")
    top_k: int = Field(10, ge=1, le=100, description="返回top-k结果")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    language: str = Field("zh-cn", description="响应语言")
    include_sources: bool = Field(True, description="是否包含来源信息")


class QueryResponse(BaseModel):
    """查询响应模型"""
    query: str = Field(..., description="原始查询")
    answer: str = Field(..., description="生成的回答")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="来源信息")
    context: str = Field("", description="使用的上下文")
    retrieval_mode: QueryMode = Field(QueryMode.HYBRID, description="检索模式")
    confidence: float = Field(0.0, description="回答置信度")
    tokens_used: int = Field(0, description="使用的Token数量")
    response_time: float = Field(0.0, description="响应时间(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    session_id: Optional[str] = Field(None, description="会话ID")
    error: Optional[str] = Field(None, description="错误信息")


# ==================== 用户和权限模型 ====================

class User(BaseSchema):
    """用户模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    role: UserRole = Field(UserRole.VIEWER, description="用户角色")
    is_active: bool = Field(True, description="是否激活")
    is_verified: bool = Field(False, description="是否验证")
    hashed_password: Optional[str] = Field(None, description="加密密码")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(0, description="登录次数")

    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('邮箱格式无效')
        return v.lower()


class Session(BaseSchema):
    """会话模型"""
    user_id: str = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="会话标题")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="消息列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="会话元数据")
    is_active: bool = Field(True, description="是否激活")
    knowledge_base_id: Optional[str] = Field(None, description="关联知识库ID")


class KnowledgeBase(BaseSchema):
    """知识库模型"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    owner_id: str = Field(..., description="所有者ID")
    is_public: bool = Field(False, description="是否公开")
    settings: Dict[str, Any] = Field(default_factory=dict, description="设置")
    document_count: int = Field(0, description="文档数量")
    chunk_count: int = Field(0, description="块数量")
    entity_count: int = Field(0, description="实体数量")
    relation_count: int = Field(0, description="关系数量")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="最后更新时间")
    tags: List[str] = Field(default_factory=list, description="标签")
    collaborators: List[str] = Field(default_factory=list, description="协作者ID列表")


# ==================== 系统配置模型 ====================

@dataclass
class RAGConfig:
    """RAG配置"""
    retrieval_mode: str = "hybrid"
    top_k: int = 10
    similarity_threshold: float = 0.7
    rerank_enabled: bool = True
    rerank_top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_doc: int = 1000
    entity_extraction: bool = True
    relation_extraction: bool = True
    graph_depth: int = 3
    min_entity_frequency: int = 2
    context_window: int = 4000
    max_context_tokens: int = 3000
    response_language: str = "zh-CN"


class SystemInfo(BaseModel):
    """系统信息模型"""
    version: str = Field(..., description="系统版本")
    status: str = Field(..., description="系统状态")
    uptime: float = Field(..., description="运行时间(秒)")
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    active_users: int = Field(..., description="活跃用户数")
    total_documents: int = Field(..., description="文档总数")
    total_queries: int = Field(..., description="查询总数")
    last_backup: Optional[datetime] = Field(None, description="最后备份时间")


# ==================== API响应模型 ====================

class APIResponse(BaseModel):
    """API响应基础模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any] = Field(..., description="数据项")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# ==================== 统计和分析模型 ====================

class UsageStats(BaseModel):
    """使用统计模型"""
    period: str = Field(..., description="统计周期")
    total_queries: int = Field(0, description="总查询数")
    unique_users: int = Field(0, description="独立用户数")
    avg_response_time: float = Field(0.0, description="平均响应时间")
    success_rate: float = Field(0.0, description="成功率")
    popular_queries: List[Dict[str, Any]] = Field(default_factory=list, description="热门查询")
    error_count: int = Field(0, description="错误数量")
    peak_concurrent_users: int = Field(0, description="峰值并发用户")


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    avg_query_time: float = Field(0.0, description="平均查询时间")
    avg_retrieval_time: float = Field(0.0, description="平均检索时间")
    avg_generation_time: float = Field(0.0, description="平均生成时间")
    cache_hit_rate: float = Field(0.0, description="缓存命中率")
    throughput: float = Field(0.0, description="吞吐量(QPS)")
    error_rate: float = Field(0.0, description="错误率")
    resource_usage: Dict[str, float] = Field(default_factory=dict, description="资源使用情况")


# ==================== 配置更新模型 ====================

class ConfigUpdate(BaseModel):
    """配置更新模型"""
    section: str = Field(..., description="配置节")
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="描述")
    user_id: str = Field(..., description="操作用户ID")


class BulkConfigUpdate(BaseModel):
    """批量配置更新模型"""
    updates: List[ConfigUpdate] = Field(..., description="配置更新列表")
    validate_only: bool = Field(False, description="仅验证不执行")


# ==================== 导出和备份模型 ====================

class ExportRequest(BaseModel):
    """导出请求模型"""
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")
    format: str = Field("json", description="导出格式")
    include_embeddings: bool = Field(False, description="是否包含向量")
    include_graph: bool = Field(True, description="是否包含知识图谱")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class BackupInfo(BaseModel):
    """备份信息模型"""
    backup_id: str = Field(..., description="备份ID")
    backup_type: str = Field(..., description="备份类型")
    file_size: int = Field(..., description="文件大小")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="备份状态")
    description: Optional[str] = Field(None, description="备份描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")