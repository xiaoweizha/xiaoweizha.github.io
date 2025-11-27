# 🔌 API 文档

企业级RAG知识库系统 RESTful API 完整文档

## 📋 API 概览

### 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (部分接口无需认证)
- **数据格式**: JSON
- **编码**: UTF-8

### 服务地址
| 服务 | 地址 | 描述 |
|------|------|------|
| **Swagger UI** | http://localhost:8000/docs | 交互式API文档 |
| **ReDoc** | http://localhost:8000/redoc | 详细API文档 |
| **OpenAPI Schema** | http://localhost:8000/openapi.json | API规范文件 |

## 🚀 快速开始

### 1. 健康检查
```bash
curl -X GET http://localhost:8000/health
```

### 2. 上传文档
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

### 3. 智能问答
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是RAG技术？",
    "mode": "hybrid",
    "top_k": 5
  }'
```

## 📚 文档管理 API

### 上传文档
上传文档到知识库，系统会自动处理并构建索引。

**端点**: `POST /api/v1/documents/upload`

**请求**:
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: <binary_file_data>
```

**支持格式**:
- PDF (.pdf)
- Word文档 (.docx, .doc)
- 文本文件 (.txt)
- Markdown文件 (.md)
- HTML文件 (.html)

**响应**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "文档上传成功，正在处理中"
}
```

**错误响应**:
```json
{
  "detail": "不支持的文件类型: .exe"
}
```

### 获取文档列表
获取已上传的文档列表，支持分页和状态过滤。

**端点**: `GET /api/v1/documents/`

**查询参数**:
- `page` (int, 默认=1): 页码
- `size` (int, 默认=20): 每页数量
- `status` (str, 可选): 文档状态过滤 (processing, processed, failed)

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/?page=1&size=10&status=processed" \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "RAG技术介绍",
      "filename": "rag_intro.pdf",
      "file_size": 1024000,
      "mime_type": "application/pdf",
      "status": "processed",
      "created_at": 1700000000.0,
      "processed_at": 1700000100.0
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 获取文档详情
根据文档ID获取详细信息。

**端点**: `GET /api/v1/documents/{document_id}`

**路径参数**:
- `document_id` (str): 文档唯一标识

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/documents/doc1 \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "RAG技术介绍",
  "filename": "rag_intro.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "status": "processed",
  "created_at": 1700000000.0,
  "processed_at": 1700000100.0
}
```

### 删除文档
根据文档ID删除文档及其相关索引。

**端点**: `DELETE /api/v1/documents/{document_id}`

**路径参数**:
- `document_id` (str): 文档唯一标识

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/doc1 \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "message": "文档删除成功"
}
```

## 💬 智能问答 API

### RAG查询 (无需认证)
基于知识库内容的智能问答，无需认证，用于快速体验。

**端点**: `POST /api/v1/chat/query`

**请求体**:
```json
{
  "query": "什么是RAG技术？",
  "mode": "hybrid",
  "top_k": 5
}
```

**参数说明**:
- `query` (str, 必需): 用户问题
- `mode` (str, 默认="hybrid"): 检索模式
  - `local`: 局部检索
  - `global`: 全局检索
  - `hybrid`: 混合检索 (推荐)
- `top_k` (int, 默认=5): 检索文档数量

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Claude API如何集成？",
    "mode": "hybrid",
    "top_k": 3
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "answer": "Claude API可以通过两种方式集成：1. 使用本机Claude CLI命令... 2. 使用传统的HTTP API调用...",
    "sources": [
      {
        "content": "文档片段内容...",
        "metadata": {
          "document_id": "doc1",
          "chunk_id": "chunk_001",
          "score": 0.95
        }
      }
    ],
    "confidence": 0.92,
    "query_time": 1.23
  },
  "message": "查询成功"
}
```

### 智能问答 (需要认证)
需要认证的智能问答接口，支持会话管理。

**端点**: `POST /api/v1/chat/ask`

**请求头**:
```
Authorization: Bearer your-token
Content-Type: application/json
```

**请求体**:
```json
{
  "message": "请介绍一下向量数据库",
  "session_id": "session_123",
  "mode": "hybrid",
  "top_k": 5
}
```

**参数说明**:
- `message` (str, 必需): 用户消息
- `session_id` (str, 可选): 会话ID，用于多轮对话
- `mode` (str, 默认="hybrid"): 检索模式
- `top_k` (int, 默认=5): 检索文档数量

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "向量数据库有什么优势？",
    "session_id": "session_456",
    "mode": "hybrid",
    "top_k": 5
  }'
```

**响应**:
```json
{
  "answer": "向量数据库的主要优势包括：1. 高效的相似性搜索...",
  "sources": [
    {
      "content": "向量数据库是专门用于存储和检索向量数据的数据库...",
      "metadata": {
        "document_id": "doc2",
        "chunk_id": "chunk_005",
        "score": 0.88
      }
    }
  ],
  "confidence": 0.89,
  "query_time": 0.95
}
```

### 获取聊天会话列表
获取用户的聊天会话历史。

**端点**: `GET /api/v1/chat/sessions`

**请求头**:
```
Authorization: Bearer your-token
```

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "sessions": [
    {
      "session_id": "session1",
      "title": "RAG技术咨询",
      "last_message": "什么是RAG技术？",
      "created_at": 1700000000.0,
      "updated_at": 1700001800.0
    }
  ],
  "total": 1
}
```

### 获取聊天会话详情
获取特定会话的消息历史。

**端点**: `GET /api/v1/chat/sessions/{session_id}`

**路径参数**:
- `session_id` (str): 会话唯一标识

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/chat/sessions/session1 \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "session_id": "session1",
  "messages": [
    {
      "role": "user",
      "content": "什么是RAG技术？",
      "timestamp": 1700000000.0
    },
    {
      "role": "assistant",
      "content": "RAG（检索增强生成）是一种结合了信息检索和生成式AI的技术...",
      "timestamp": 1700000010.0
    }
  ],
  "created_at": 1700000000.0
}
```

### 删除聊天会话
删除指定的聊天会话。

**端点**: `DELETE /api/v1/chat/sessions/{session_id}`

**路径参数**:
- `session_id` (str): 会话唯一标识

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/chat/sessions/session1 \
  -H "Authorization: Bearer your-token"
```

**响应**:
```json
{
  "message": "聊天会话删除成功"
}
```

## 🔐 认证 API

### 获取访问令牌
用于获取API访问令牌。

**端点**: `POST /api/v1/auth/token`

**请求体**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 📊 系统状态 API

### 健康检查
检查系统运行状态和各组件连接情况。

**端点**: `GET /health`

**请求示例**:
```bash
curl -X GET http://localhost:8000/health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": 1700000000.0,
  "version": "1.0.0",
  "components": {
    "mongodb": "connected",
    "redis": "connected",
    "qdrant": "connected",
    "neo4j": "connected",
    "llm_provider": "available"
  }
}
```

### 系统信息
获取系统配置和统计信息。

**端点**: `GET /system/info`

**请求示例**:
```bash
curl -X GET http://localhost:8000/system/info
```

**响应**:
```json
{
  "system": {
    "name": "企业级RAG知识库系统",
    "version": "1.0.0",
    "environment": "development"
  },
  "llm": {
    "provider": "claude",
    "model": "claude-3-5-sonnet-20241022",
    "status": "available"
  },
  "databases": {
    "mongodb": "connected",
    "redis": "connected",
    "qdrant": "connected",
    "neo4j": "connected"
  },
  "statistics": {
    "total_documents": 15,
    "total_chunks": 1250,
    "total_entities": 385,
    "total_relations": 742
  }
}
```

## ⚡ 数据模型

### Document (文档)
```json
{
  "id": "string (UUID)",
  "title": "string",
  "filename": "string",
  "file_path": "string",
  "file_size": "integer",
  "mime_type": "string",
  "status": "processing|processed|failed",
  "author": "string",
  "created_at": "float (timestamp)",
  "processed_at": "float (timestamp, optional)",
  "metadata": "object"
}
```

### QueryRequest (查询请求)
```json
{
  "query": "string (required)",
  "mode": "local|global|hybrid (default: hybrid)",
  "top_k": "integer (default: 5)",
  "filters": "object (optional)"
}
```

### QueryResponse (查询响应)
```json
{
  "answer": "string",
  "sources": [
    {
      "content": "string",
      "metadata": {
        "document_id": "string",
        "chunk_id": "string",
        "score": "float"
      }
    }
  ],
  "confidence": "float (0-1)",
  "query_time": "float (seconds)"
}
```

### ChatMessage (聊天消息)
```json
{
  "role": "user|assistant|system",
  "content": "string",
  "timestamp": "float (timestamp)"
}
```

## ❌ 错误处理

### HTTP状态码
- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权 (需要登录)
- `403` - 禁止访问 (权限不足)
- `404` - 资源不存在
- `413` - 文件太大
- `422` - 请求数据验证失败
- `500` - 服务器内部错误

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

### 常见错误示例

**文件太大**:
```json
{
  "detail": "文件大小超过限制 (50MB)"
}
```

**不支持的文件格式**:
```json
{
  "detail": "不支持的文件类型: .exe"
}
```

**Claude API调用失败**:
```json
{
  "detail": "查询失败: Claude API响应为空"
}
```

**认证失败**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

## 🎯 使用示例

### Python 客户端示例
```python
import requests
import json

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def upload_document(self, file_path):
        """上传文档"""
        url = f"{self.base_url}/api/v1/documents/upload"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(url, files=files)
        return response.json()

    def ask_question(self, query, mode="hybrid"):
        """智能问答"""
        url = f"{self.base_url}/api/v1/chat/query"
        data = {
            "query": query,
            "mode": mode,
            "top_k": 5
        }
        response = self.session.post(url, json=data)
        return response.json()

# 使用示例
client = RAGClient()

# 上传文档
result = client.upload_document("document.pdf")
print(f"文档ID: {result['document_id']}")

# 智能问答
response = client.ask_question("什么是RAG技术？")
print(f"回答: {response['data']['answer']}")
```

### JavaScript 客户端示例
```javascript
class RAGClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/api/v1/documents/upload`, {
            method: 'POST',
            body: formData
        });

        return response.json();
    }

    async askQuestion(query, mode = 'hybrid') {
        const response = await fetch(`${this.baseUrl}/api/v1/chat/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                mode: mode,
                top_k: 5
            })
        });

        return response.json();
    }
}

// 使用示例
const client = new RAGClient();

// 上传文档
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    const result = await client.uploadDocument(file);
    console.log('文档ID:', result.document_id);
});

// 智能问答
async function askQuestion() {
    const query = document.getElementById('queryInput').value;
    const response = await client.askQuestion(query);
    console.log('回答:', response.data.answer);
}
```

## 📞 技术支持

- **Swagger UI**: http://localhost:8000/docs - 交互式API测试
- **API Schema**: http://localhost:8000/openapi.json - OpenAPI 3.0规范
- **项目仓库**: https://github.com/xiaoweizha/xiaoweizha.github.io
- **问题反馈**: [GitHub Issues](https://github.com/xiaoweizha/xiaoweizha.github.io/issues)

---

**最后更新**: 2024年11月27日
**文档版本**: v1.0.0
**API版本**: v1