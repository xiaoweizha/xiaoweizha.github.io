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
# 安装Python依赖
pip3 install -r requirements.txt

# Claude API配置（推荐使用本机CLI）
# 安装Claude CLI（如果尚未安装）
curl -sSf https://install.anthropic.com | sh

# 或者使用传统API密钥方式：
# cp .env.production .env
# vim .env  # 设置 ANTHROPIC_API_KEY=your-key-here
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
| **🏠 Web界面** | http://localhost:8000 | RAG知识库主界面 |
| **📤 文档上传** | http://localhost:8000/#upload | 上传文档页面 |
| **💬 智能问答** | http://localhost:8000/#chat | 问答聊天界面 |
| **📚 API文档** | http://localhost:8000/docs | 接口文档 |
| **💚 健康检查** | http://localhost:8000/health | 系统状态 |

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

# 测试文档上传
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.txt"

# 测试问答功能
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是RAG技术？"}'

# 使用工具检查知识库
python3 test_kb.py
```

## 🛠️ 管理命令

### 服务管理
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

### 工具脚本
```bash
# 查看上传的文档
python3 list_documents.py

# 查看知识图谱数据
python3 view_graph.py

# 测试知识库功能
python3 test_kb.py
```

## ❓ 常见问题

**Q: 端口被占用怎么办？**
```bash
# 检查端口
lsof -i :8000
# 杀死占用进程或修改配置文件端口
```

**Q: Claude API调用失败？**
```bash
# 方法1: 检查本机Claude CLI
which claude

# 方法2: 检查API密钥配置
grep ANTHROPIC_API_KEY .env

# 测试Claude连接
python3 -c "from src.core.llm_providers import ClaudeProvider; import asyncio; print(asyncio.run(ClaudeProvider().generate_response('hello')))"
```

**Q: 内存不够？**
```bash
# 仅启动核心服务（最小内存占用）
./scripts/start-services.sh core -d
```

---

📖 **完整文档**: [DEPLOYMENT.md](./DEPLOYMENT.md)
🔗 **项目地址**: https://github.com/xiaoweizha/xiaoweizha.github.io