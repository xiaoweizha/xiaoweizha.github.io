# 企业级RAG知识库系统 - 部署指南

## 📋 系统概述

企业级RAG（Retrieval-Augmented Generation）知识库系统是一个基于LightRAG架构的智能问答平台，支持多模态检索、知识图谱构建和企业级安全管控。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web前端界面    │    │   Nginx代理     │    │   监控面板      │
│   (Port 3000)   │    │   (Port 80/443) │    │   (Port 3001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────────┐
                    │   FastAPI 应用   │
                    │   (Port 8000)   │
                    └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MongoDB    │    │    Redis     │    │   Qdrant     │
│  (27017)     │    │   (6379)     │    │   (6333)     │
│  文档存储     │    │   缓存       │    │  向量数据库   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Elasticsearch │    │    Neo4j     │    │    MinIO     │
│  (9200)      │    │ (7474/7687)  │    │ (9000/9001) │
│  全文检索     │    │  知识图谱     │    │  对象存储     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 🧩 系统组件

### 核心组件（必需）

| 组件 | 端口 | 用途 | 状态 |
|------|------|------|------|
| **FastAPI 应用** | 8000 | RAG API服务，核心业务逻辑 | 🔴 必需 |
| **MongoDB** | 27017 | 文档和元数据存储 | 🔴 必需 |
| **Redis** | 6379 | 缓存、会话存储 | 🔴 必需 |
| **Qdrant** | 6333 | 向量数据库，语义检索 | 🔴 必需 |

### 增强组件（可选）

| 组件 | 端口 | 用途 | 状态 |
|------|------|------|------|
| **Elasticsearch** | 9200 | 全文检索引擎 | 🟡 推荐 |
| **Neo4j** | 7474/7687 | 知识图谱存储 | 🟡 推荐 |
| **MinIO** | 9000/9001 | 对象存储，文件管理 | 🟢 可选 |

### 运维组件（推荐）

| 组件 | 端口 | 用途 | 状态 |
|------|------|------|------|
| **Nginx** | 80/443 | 反向代理、负载均衡、SSL终端 | 🟡 推荐 |
| **Prometheus** | 9090 | 指标收集和监控 | 🟡 推荐 |
| **Grafana** | 3001 | 监控面板和可视化 | 🟡 推荐 |

## 🚀 快速部署

### 1. 环境要求

#### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+) / macOS / Windows WSL2
- **内存**: 最低 8GB，推荐 16GB+
- **存储**: 最低 50GB 可用空间
- **网络**: 稳定的互联网连接

#### 软件依赖
```bash
# 必需软件
Docker >= 20.0.0
Docker Compose >= 2.0.0
Git >= 2.30.0

# 可选软件（单机部署）
Python >= 3.9
Node.js >= 18.0.0 (前端构建)
```

### 2. 获取代码

```bash
# 克隆仓库
git clone https://github.com/xiaoweizha/xiaoweizha.github.io.git
cd xiaoweizha.github.io

# 检查项目结构
ls -la
```

### 3. 配置环境

#### 3.1 基础配置
```bash
# 复制环境配置
cp .env.production .env

# 编辑配置文件（重要！）
vim .env
```

#### 3.2 Claude API配置
```bash
# === Claude CLI方式（推荐）===
# 系统会自动检测本机安装的Claude CLI
# 安装Claude CLI：
# curl -sSf https://install.anthropic.com | sh

# === 传统API方式（备用）===
ANTHROPIC_API_KEY=your-claude-api-key-here
ANTHROPIC_BASE_URL=https://api.anthropic.com

# === 数据库密码（生产环境必须修改） ===
MONGODB_PASSWORD=your-strong-mongodb-password
REDIS_PASSWORD=your-strong-redis-password
NEO4J_PASSWORD=your-strong-neo4j-password

# === 应用安全（生产环境必须修改） ===
JWT_SECRET_KEY=your-super-secret-jwt-key-256-bit-random-string
SECRET_KEY=your-application-secret-key-also-very-long-and-random

# === 域名配置（可选） ===
DOMAIN=your-domain.com
SSL_ENABLED=true
```

### 4. 部署方式选择

#### 方式 A：一键快速部署（推荐新手）

```bash
# 1. 启动依赖服务
chmod +x scripts/start-services.sh
./scripts/start-services.sh core -d

# 2. 安装Python依赖
pip3 install -r requirements.txt

# 3. 等待服务启动（约2-5分钟）
./scripts/start-services.sh status

# 4. 启动应用
python3 main.py
```

#### 方式 B：完整服务部署（推荐生产）

```bash
# 启动完整服务栈
./scripts/start-services.sh full -d

# 生产环境部署（包含监控）
chmod +x scripts/deploy-production.sh
./scripts/deploy-production.sh docker --monitoring

# 启用SSL（可选）
./scripts/deploy-production.sh docker --ssl -d your-domain.com
```

#### 方式 C：单机部署（资源受限）

```bash
# 安装Python依赖
pip3 install -r requirements.txt

# 仅启动必需数据库
docker run -d --name rag-mongodb -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:6.0

docker run -d --name rag-redis -p 6379:6379 \
  redis:7-alpine redis-server --requirepass password123

docker run -d --name rag-qdrant -p 6333:6333 \
  qdrant/qdrant:latest

# 启动应用
python3 main.py
```

## 📍 访问地址

### 主要服务

| 服务 | 地址 | 用途 | 认证 |
|------|------|------|------|
| **Web界面** | http://localhost:8000 | RAG知识库Web界面 | - |
| **文档上传** | http://localhost:8000/#upload | 文档上传页面 | - |
| **智能问答** | http://localhost:8000/#chat | 智能问答界面 | - |
| **API文档** | http://localhost:8000/docs | Swagger API文档 | - |
| **健康检查** | http://localhost:8000/health | 系统健康状态 | - |

### 数据库管理

| 服务 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| **MongoDB** | localhost:27017 | admin | password123 |
| **Redis** | localhost:6379 | - | password123 |
| **Qdrant Web UI** | http://localhost:6333/dashboard | - | - |
| **Neo4j Browser** | http://localhost:7474 | neo4j | password123 |
| **MinIO Console** | http://localhost:9001 | admin | password123 |

### 监控和运维

| 服务 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| **Grafana** | http://localhost:3001 | admin | admin123 |
| **Prometheus** | http://localhost:9090 | - | - |
| **Elasticsearch** | http://localhost:9200 | - | - |

### 生产环境（SSL启用后）

| 服务 | 地址 | 说明 |
|------|------|------|
| **主应用** | https://your-domain.com | HTTPS访问 |
| **API** | https://your-domain.com/api | API接口 |
| **监控** | https://your-domain.com:3001 | Grafana面板 |

## 🔍 部署验证

### 1. 服务状态检查

```bash
# 检查所有容器状态
docker ps

# 检查特定服务
./scripts/start-services.sh status

# 查看服务日志
./scripts/start-services.sh logs [服务名]
```

### 2. 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 文档上传测试
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.txt"

# 智能问答测试
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是RAG技术？"}'

# 知识库状态检查
python3 test_kb.py
```

### 3. 预期响应

#### 健康检查响应
```json
{
  "status": "healthy",
  "timestamp": 1700000000.0,
  "version": "1.0.0",
  "components": {
    "mongodb": "connected",
    "redis": "connected",
    "qdrant": "connected",
    "llm_provider": "available"
  }
}
```

#### 系统信息响应
```json
{
  "system": {
    "name": "企业级RAG知识库系统",
    "version": "1.0.0",
    "environment": "production"
  },
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022"
  },
  "databases": {
    "mongodb": "connected",
    "redis": "connected",
    "qdrant": "connected"
  }
}
```

## 🧰 工具脚本使用

### 文档管理工具

```bash
# 查看已上传的文档列表
python3 list_documents.py

# 查看特定文档详情
python3 list_documents.py <document_id>
```

### 知识图谱查看工具

```bash
# 查看完整图谱统计和数据
python3 view_graph.py

# 搜索特定实体
python3 view_graph.py "机器学习"

# 简化版图谱查看（Neo4j连接问题时使用）
python3 simple_graph_view.py
```

### 知识库测试工具

```bash
# 测试知识库是否正常工作
python3 test_kb.py
```

## 🛠️ 运维管理

### 启动和停止

```bash
# 启动服务
./scripts/start-services.sh core -d          # 核心服务
./scripts/start-services.sh full -d          # 完整服务

# 停止服务
./scripts/start-services.sh stop

# 重启服务
./scripts/start-services.sh restart

# 查看状态
./scripts/start-services.sh status
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f mongodb
docker-compose -f docker-compose.dev.yml logs -f rag-api

# 查看应用日志
tail -f logs/app.log
```

### 数据备份

```bash
# 备份MongoDB
docker exec rag-mongodb-dev mongodump --out /tmp/backup
docker cp rag-mongodb-dev:/tmp/backup ./backup/mongodb-$(date +%Y%m%d)

# 备份向量数据
docker cp rag-qdrant-dev:/qdrant/storage ./backup/qdrant-$(date +%Y%m%d)

# 备份Redis
docker exec rag-redis-dev redis-cli SAVE
docker cp rag-redis-dev:/data/dump.rdb ./backup/redis-$(date +%Y%m%d).rdb
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看系统资源
htop
df -h
free -h

# 查看网络连接
netstat -tulnp | grep :8000
```

## ⚠️ 常见问题

### 1. 端口冲突

**问题**: 端口已被占用
```bash
Error: bind: address already in use
```

**解决**:
```bash
# 查看端口占用
lsof -i :8000
netstat -tulnp | grep :8000

# 修改配置文件中的端口
vim .env
```

### 2. 内存不足

**问题**: Elasticsearch启动失败
```bash
ERROR: Elasticsearch exited unexpectedly
```

**解决**:
```bash
# 降低Elasticsearch内存使用
export ES_JAVA_OPTS="-Xms512m -Xmx512m"

# 或者禁用Elasticsearch
./scripts/start-services.sh core -d  # 仅启动核心服务
```

### 3. Claude API配置

**问题**: Claude API调用失败
```bash
HTTP 401: Invalid API key 或 Claude响应为空
```

**解决**:
```bash
# 方案1: 使用本机Claude CLI（推荐）
which claude
# 如果没有安装，运行：
curl -sSf https://install.anthropic.com | sh

# 方案2: 检查API密钥配置
echo $ANTHROPIC_API_KEY
vim .env

# 测试Claude连接
python3 -c "from src.core.llm_providers import ClaudeProvider; import asyncio; print(asyncio.run(ClaudeProvider().generate_response('hello')))"
```

### 4. 数据库连接失败

**问题**: 数据库连接超时
```bash
Connection timeout to MongoDB
```

**解决**:
```bash
# 检查容器状态
docker ps | grep mongo

# 检查网络连通性
docker exec rag-api-container ping mongodb

# 查看数据库日志
docker logs rag-mongodb-dev
```

## 📚 更多资源

- **项目仓库**: https://github.com/xiaoweizha/xiaoweizha.github.io
- **API文档**: http://localhost:8000/docs
- **技术支持**: [GitHub Issues](https://github.com/xiaoweizha/xiaoweizha.github.io/issues)
- **部署脚本**: `scripts/deploy-production.sh --help`
- **配置说明**: `config/config.yaml`

## 📞 技术支持

如遇到部署问题，请按以下方式获取支持：

1. **检查日志**: 查看具体错误信息
2. **查阅文档**: 参考本部署指南
3. **社区支持**: 提交GitHub Issue
4. **系统诊断**: 运行健康检查命令

---

**最后更新**: 2024年11月26日
**文档版本**: v1.0.0
**适用系统版本**: 企业级RAG知识库系统 v1.0.0