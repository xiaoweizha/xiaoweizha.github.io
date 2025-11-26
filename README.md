# 企业级RAG知识库系统

基于LightRAG的企业级检索增强生成（RAG）知识库系统，使用中文作为第一语言，专为企业场景设计。

## 系统概述

本系统是一个完整的企业级RAG解决方案，集成了知识图谱、向量检索、多模态处理等先进技术，为企业提供智能化的知识管理和问答服务。

## 核心特性

### 🚀 核心功能
- **多模式检索**: 向量检索、图检索、混合检索
- **知识图谱**: 自动构建实体关系图谱
- **多模态支持**: 文档、图片、音视频处理
- **智能问答**: 基于检索增强的对话生成
- **实时更新**: 增量学习与知识库动态更新

### 🏢 企业级特性
- **权限管理**: 细粒度的用户权限控制
- **数据安全**: 端到端加密与访问控制
- **高可用性**: 分布式架构与负载均衡
- **监控分析**: 全链路监控与使用统计
- **API集成**: RESTful API与企业系统集成

### 📊 可观测性
- **实时监控**: 系统性能与用户行为监控
- **使用分析**: 知识库使用统计与优化建议
- **审计日志**: 完整的操作记录与合规支持

## 技术架构

### 存储层
```
├── 文档存储 (Document Store)
│   ├── MongoDB - 原始文档存储
│   ├── MinIO - 文件对象存储
│   └── Redis - 缓存加速
├── 向量存储 (Vector Store)
│   ├── Qdrant - 主向量数据库
│   └── Elasticsearch - 文本检索增强
└── 图存储 (Graph Store)
    ├── Neo4j - 知识图谱存储
    └── NetworkX - 图计算引擎
```

### 服务层
```
├── 核心RAG服务 (Core RAG)
│   ├── 文档处理服务
│   ├── 向量检索服务
│   ├── 图谱查询服务
│   └── 生成增强服务
├── 知识管理服务 (Knowledge Management)
│   ├── 文档上传与解析
│   ├── 知识图谱构建
│   ├── 增量更新管理
│   └── 数据质量控制
├── 用户服务 (User Service)
│   ├── 身份认证
│   ├── 权限管理
│   ├── 用户偏好
│   └── 使用统计
└── 系统服务 (System Service)
    ├── 监控告警
    ├── 日志审计
    ├── 配置管理
    └── 健康检查
```

### 应用层
```
├── Web应用 (Web Application)
│   ├── 管理后台 - React + TypeScript
│   ├── 用户前端 - Vue.js + Element Plus
│   └── 移动端 - React Native
├── API网关 (API Gateway)
│   ├── 路由转发
│   ├── 认证鉴权
│   ├── 限流熔断
│   └── 监控统计
└── 企业集成 (Enterprise Integration)
    ├── SSO单点登录
    ├── LDAP目录服务
    ├── 企业微信/钉钉
    └── 现有业务系统
```

## 🚀 快速开始

### 📖 部署指南

- **🚀 [5分钟快速启动](./QUICK_START.md)** - 最简单的部署方式
- **📋 [详细部署指南](./DEPLOYMENT.md)** - 完整的生产环境部署
- **🛠️ [生产环境指南](./scripts/production-deploy-guide.md)** - 企业级部署方案

### ⚡ 一键部署

```bash
# 1. 获取代码
git clone https://github.com/xiaoweizha/xiaoweizha.github.io.git
cd xiaoweizha.github.io

# 2. 配置环境
cp .env.production .env
# 编辑 .env 文件，设置 ANTHROPIC_AUTH_TOKEN

# 3. 启动服务
./scripts/start-services.sh core -d
python3 main.py

# 4. 访问系统
# 主页: http://localhost:8000
# API: http://localhost:8000/docs
```

### 💻 环境要求
- Python 3.9+
- Docker & Docker Compose
- 8GB+ 内存（推荐16GB+）
- Claude API密钥

### 配置说明

#### 基础配置 (config/config.yaml)
```yaml
# 系统配置
system:
  name: "企业RAG知识库"
  version: "1.0.0"
  debug: false

# LLM配置
llm:
  provider: "openai"  # openai, azure, qianfan, tongyi
  model: "gpt-4-turbo"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.1

# 向量模型配置
embedding:
  provider: "openai"  # openai, huggingface, bge
  model: "text-embedding-3-large"
  dimension: 1536

# 数据库配置
database:
  mongodb:
    host: "localhost"
    port: 27017
    database: "rag_kb"
  neo4j:
    uri: "bolt://localhost:7687"
    username: "neo4j"
    password: "password"
  qdrant:
    host: "localhost"
    port: 6333
```

## 使用指南

### 1. 知识库管理

#### 文档上传
```python
from rag_system import KnowledgeBase

kb = KnowledgeBase()

# 上传单个文档
result = kb.upload_document("path/to/document.pdf")

# 批量上传
result = kb.batch_upload("path/to/documents/")

# 支持格式：PDF, DOCX, TXT, MD, HTML, PPT, XLS
```

#### 知识图谱构建
```python
# 自动构建知识图谱
kb.build_knowledge_graph(
    extract_entities=True,
    extract_relations=True,
    merge_similar=True
)

# 查看图谱统计
stats = kb.get_graph_stats()
print(f"实体数量: {stats['entities']}")
print(f"关系数量: {stats['relations']}")
```

### 2. 智能问答

#### 基础问答
```python
from rag_system import ChatBot

bot = ChatBot()

# 单轮问答
answer = bot.ask("什么是RAG技术？")

# 多轮对话
session = bot.create_session()
answer1 = session.ask("介绍一下机器学习")
answer2 = session.ask("它有哪些应用场景？")
```

#### 高级检索
```python
# 混合检索
result = bot.hybrid_search(
    query="深度学习在NLP中的应用",
    retrieval_mode="hybrid",  # local, global, hybrid
    top_k=10,
    rerank=True
)

# 多模态检索
result = bot.multimodal_search(
    text_query="产品架构图",
    image_query="path/to/reference.jpg"
)
```

### 3. 系统管理

#### 用户权限
```python
from rag_system import UserManager

um = UserManager()

# 创建用户
user = um.create_user(
    username="张三",
    email="zhangsan@company.com",
    role="knowledge_worker"
)

# 设置权限
um.set_permissions(user.id, {
    "read_knowledge": True,
    "write_knowledge": False,
    "manage_users": False
})
```

#### 监控分析
```python
from rag_system import Analytics

analytics = Analytics()

# 使用统计
stats = analytics.get_usage_stats(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# 性能监控
metrics = analytics.get_performance_metrics()
```

## API文档

### RESTful API

#### 文档管理
```http
# 上传文档
POST /api/v1/documents
Content-Type: multipart/form-data

# 获取文档列表
GET /api/v1/documents?page=1&size=20

# 删除文档
DELETE /api/v1/documents/{document_id}
```

#### 问答接口
```http
# 提问
POST /api/v1/chat/ask
{
  "query": "什么是RAG？",
  "mode": "hybrid",
  "top_k": 5
}

# 会话管理
POST /api/v1/chat/sessions
GET /api/v1/chat/sessions/{session_id}/messages
```

#### 知识图谱
```http
# 获取实体
GET /api/v1/graph/entities?search=机器学习

# 获取关系
GET /api/v1/graph/relations/{entity_id}

# 图谱搜索
POST /api/v1/graph/search
{
  "query": "深度学习相关技术",
  "max_depth": 3
}
```

### WebSocket API

#### 实时对话
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'answer') {
        console.log('回答:', data.content);
    }
};

ws.send(JSON.stringify({
    type: 'question',
    content: '什么是RAG技术？'
}));
```

## 部署指南

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  rag-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - NEO4J_URI=bolt://neo4j:7687
      - QDRANT_HOST=qdrant
    depends_on:
      - mongo
      - neo4j
      - qdrant

  mongo:
    image: mongo:6.0
    volumes:
      - mongo_data:/data/db

  neo4j:
    image: neo4j:5.0
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  mongo_data:
  neo4j_data:
  qdrant_data:
```

### Kubernetes部署

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: enterprise-rag

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
  namespace: enterprise-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: rag-api
        image: enterprise-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          value: "mongodb://mongo-service:27017"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-api-service
  namespace: enterprise-rag
spec:
  selector:
    app: rag-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 性能优化

### 1. 检索优化
- 向量索引优化：使用HNSW算法提升检索速度
- 缓存策略：热点查询结果缓存
- 并行检索：向量检索与图检索并行执行

### 2. 存储优化
- 文档分片：大文档自动分片处理
- 压缩存储：向量数据压缩存储
- 冷热分离：访问频率自动分层存储

### 3. 计算优化
- GPU加速：向量计算GPU加速
- 模型优化：embedding模型量化
- 批处理：批量文档处理提升吞吐

## 安全说明

### 数据安全
- 端到端加密：传输和存储全程加密
- 访问控制：基于角色的权限管理
- 审计日志：完整的操作记录

### 隐私保护
- 数据脱敏：敏感信息自动识别和脱敏
- 本地部署：支持完全本地化部署
- 合规支持：符合GDPR、等保等合规要求

## 监控运维

### 监控指标
- 系统指标：CPU、内存、磁盘、网络
- 业务指标：QPS、响应时间、成功率
- 用户指标：活跃用户数、使用频次

### 告警配置
- 性能告警：响应时间超阈值告警
- 错误告警：错误率超阈值告警
- 容量告警：存储空间不足告警

## 发展路线图

### v1.0 (当前版本)
- ✅ 基础RAG功能
- ✅ 知识图谱构建
- ✅ Web管理界面
- ✅ API服务

### v1.1 (规划中)
- 🔄 多模态处理增强
- 🔄 实时学习能力
- 🔄 联邦学习支持
- 🔄 更多LLM支持

### v2.0 (未来版本)
- 📋 Agent能力集成
- 📋 工作流编排
- 📋 插件生态系统
- 📋 行业解决方案

## 贡献指南

### 开发环境
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements-dev.txt
pre-commit install

# 运行测试
pytest tests/

# 代码检查
flake8 src/
black src/
```

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建配置
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 项目主页: https://github.com/xiaoweizha/enterprise-rag
- 问题反馈: https://github.com/xiaoweizha/enterprise-rag/issues
- 邮件联系: support@xiaoweizha.com
- 企业服务: enterprise@xiaoweizha.com

## 致谢

- [LightRAG](https://github.com/HKUDS/LightRAG) - 核心RAG框架
- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [Neo4j](https://github.com/neo4j/neo4j) - 图数据库
- 开源社区的所有贡献者