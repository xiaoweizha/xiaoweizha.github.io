# 🚀 企业级RAG知识库系统 - 快速启动指南

> 5分钟快速部署企业级RAG系统

## 📦 一键部署

### 1. 获取代码
```bash
git clone https://github.com/xiaoweizha/xiaoweizha.github.io.git
cd xiaoweizha.github.io
```

### 2. 配置环境
```bash
# 复制配置文件
cp .env.production .env

# 编辑配置（必须设置API密钥）
vim .env
# 修改以下配置：
# ANTHROPIC_AUTH_TOKEN=your-claude-api-key-here
```

### 3. 启动服务
```bash
# 启动核心数据库
./scripts/start-services.sh core -d

# 启动RAG应用
python3 main.py
```

## 🎯 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **🏠 主页** | http://localhost:8000 | RAG知识库界面 |
| **📚 API文档** | http://localhost:8000/docs | 接口文档 |
| **💚 健康检查** | http://localhost:8000/health | 系统状态 |
| **🗄️ Qdrant UI** | http://localhost:6333/dashboard | 向量数据库 |

## 🔧 必需组件

### 核心服务（自动启动）
- **MongoDB** (localhost:27017) - 文档存储
- **Redis** (localhost:6379) - 缓存
- **Qdrant** (localhost:6333) - 向量数据库
- **FastAPI** (localhost:8000) - RAG应用

### 可选增强服务
```bash
# 启动完整服务（包含Elasticsearch、Neo4j等）
./scripts/start-services.sh full -d
```

## ✅ 验证部署

```bash
# 检查服务状态
curl http://localhost:8000/health

# 测试问答功能
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是RAG技术？"}'
```

## 🛠️ 管理命令

```bash
# 查看状态
./scripts/start-services.sh status

# 查看日志
./scripts/start-services.sh logs

# 停止服务
./scripts/start-services.sh stop

# 重启服务
./scripts/start-services.sh restart
```

## ❓ 常见问题

**Q: 端口被占用怎么办？**
```bash
# 检查端口
lsof -i :8000
# 杀死占用进程或修改配置文件端口
```

**Q: API调用失败？**
```bash
# 检查API密钥配置
grep ANTHROPIC_AUTH_TOKEN .env
# 确保设置了有效的Claude API密钥
```

**Q: 内存不够？**
```bash
# 仅启动核心服务（最小内存占用）
./scripts/start-services.sh core -d
```

---

📖 **完整文档**: [DEPLOYMENT.md](./DEPLOYMENT.md)
🔗 **项目地址**: https://github.com/xiaoweizha/xiaoweizha.github.io