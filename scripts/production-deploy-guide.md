# 企业级RAG知识库系统 - 生产环境部署指南

## 📋 部署概览

本系统支持三种生产环境部署方式：
1. **Docker Compose部署** - 推荐用于中小型部署
2. **Kubernetes部署** - 推荐用于大规模企业部署
3. **单机部署** - 适用于资源受限或测试环境

## 🚀 快速部署

### 方式1：Docker Compose部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-username/enterprise-rag-system.git
cd enterprise-rag-system

# 2. 配置环境变量
cp .env.production .env
# 编辑 .env 文件，配置您的实际参数

# 3. 一键部署
./scripts/deploy-production.sh docker --monitoring

# 4. 访问系统
# 主页: http://localhost
# API: http://localhost:8000
# 监控: http://localhost:3001
```

### 方式2：Kubernetes部署

```bash
# 1. 准备Kubernetes集群
kubectl cluster-info

# 2. 部署系统
./scripts/deploy-production.sh k8s --monitoring --scale rag-api=3

# 3. 获取访问地址
kubectl get services -n enterprise-rag
```

### 方式3：单机部署

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 启动数据服务
./scripts/deploy-production.sh standalone --backup

# 3. 启动应用
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## ⚙️ 详细配置

### 1. 环境配置

编辑 `.env.production` 文件：

```bash
# 核心配置
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# 数据库配置
MONGODB_HOST=your-mongodb-host
MONGODB_USERNAME=your-username
MONGODB_PASSWORD=your-strong-password

# LLM配置
LLM_PROVIDER=anthropic
ANTHROPIC_AUTH_TOKEN=your-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 安全配置
JWT_SECRET_KEY=your-super-secret-jwt-key
SECRET_KEY=your-application-secret-key

# SSL配置
SSL_ENABLED=true
DOMAIN=your-domain.com
```

### 2. SSL证书配置

```bash
# 自动获取Let's Encrypt证书
./scripts/deploy-production.sh docker --ssl -d your-domain.com

# 或手动配置证书
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

### 3. 监控配置

```bash
# 启用完整监控栈
./scripts/deploy-production.sh docker --monitoring

# 访问监控界面
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 🏗️ 架构组件

### 核心服务

| 服务 | 端口 | 说明 |
|------|------|------|
| RAG API | 8000 | 主要API服务 |
| Frontend | 3000 | Web前端界面 |
| Nginx | 80/443 | 反向代理和负载均衡 |

### 数据存储

| 组件 | 端口 | 用途 |
|------|------|------|
| MongoDB | 27017 | 文档和元数据存储 |
| Neo4j | 7474/7687 | 知识图谱存储 |
| Qdrant | 6333 | 向量数据库 |
| Redis | 6379 | 缓存和会话存储 |
| Elasticsearch | 9200 | 全文检索 |
| MinIO | 9000 | 对象存储 |

### 监控组件

| 组件 | 端口 | 用途 |
|------|------|------|
| Prometheus | 9090 | 指标收集 |
| Grafana | 3001 | 可视化监控 |
| AlertManager | 9093 | 告警管理 |

## 📊 性能调优

### 1. 数据库优化

```bash
# MongoDB索引优化
docker exec -it enterprise-rag-mongo mongo --eval "
db.documents.createIndex({title: 'text', content: 'text'});
db.documents.createIndex({created_at: -1});
db.documents.createIndex({user_id: 1, created_at: -1});
"

# Redis内存优化
echo "maxmemory 2gb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```

### 2. 应用扩展

```bash
# 水平扩展API服务
docker-compose up --scale rag-api=3 -d

# Kubernetes扩展
kubectl scale deployment enterprise-rag-api --replicas=5 -n enterprise-rag
```

### 3. 负载均衡配置

```nginx
# nginx/nginx.conf
upstream rag_backend {
    least_conn;
    server rag-api-1:8000 max_fails=3 fail_timeout=30s;
    server rag-api-2:8000 max_fails=3 fail_timeout=30s;
    server rag-api-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://rag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 缓存设置
        proxy_cache_bypass $http_upgrade;
        proxy_no_cache $http_pragma $http_authorization;
    }
}
```

## 🔒 安全配置

### 1. 网络安全

```yaml
# docker-compose安全配置
networks:
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge

services:
  rag-api:
    networks:
      - internal
      - external

  mongo:
    networks:
      - internal  # 仅内网访问
```

### 2. 访问控制

```bash
# 配置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 27017/tcp  # 禁止外网访问MongoDB
ufw enable
```

### 3. 认证和授权

```python
# JWT配置
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 角色权限配置
RBAC_ENABLED=true
DEFAULT_USER_ROLE=viewer
ADMIN_USERS=["admin@company.com"]
```

## 📈 监控和告警

### 1. 关键指标监控

```yaml
# 主要监控指标
- API响应时间和错误率
- 数据库连接数和查询性能
- 向量检索延迟和准确率
- LLM调用成功率和token使用量
- 系统资源使用率（CPU、内存、磁盘）
```

### 2. 告警配置

```yaml
# Prometheus告警规则
groups:
- name: rag-system
  rules:
  - alert: APIHighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    annotations:
      summary: "API error rate is high"

  - alert: DatabaseConnectionHigh
    expr: mongodb_connections_current > 80
    for: 5m
    annotations:
      summary: "MongoDB connection count is high"
```

### 3. 日志聚合

```bash
# 集中日志收集
docker run -d \
  --name filebeat \
  --user root \
  -v /var/log:/var/log:ro \
  -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  elastic/filebeat:8.11.0
```

## 🔄 备份和恢复

### 1. 数据备份

```bash
# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# MongoDB备份
mongodump --host mongo:27017 --out $BACKUP_DIR/mongodb

# 向量数据备份
tar -czf $BACKUP_DIR/qdrant.tar.gz /var/lib/qdrant/storage

# 上传到云存储
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/$(date +%Y%m%d)
```

### 2. 灾难恢复

```bash
# 数据恢复脚本
#!/bin/bash
RESTORE_DATE=$1
RESTORE_DIR="/backup/$RESTORE_DATE"

# 恢复MongoDB
mongorestore --host mongo:27017 $RESTORE_DIR/mongodb

# 恢复向量数据
tar -xzf $RESTORE_DIR/qdrant.tar.gz -C /var/lib/qdrant/
```

## 🚨 故障排除

### 1. 常见问题

```bash
# 查看服务状态
docker-compose ps
kubectl get pods -n enterprise-rag

# 查看日志
docker-compose logs -f rag-api
kubectl logs -f deployment/enterprise-rag-api -n enterprise-rag

# 健康检查
curl http://localhost:8000/health
```

### 2. 性能问题诊断

```bash
# 查看资源使用
docker stats
kubectl top pods -n enterprise-rag

# 数据库性能
docker exec -it mongo mongostat
docker exec -it redis redis-cli info stats
```

### 3. 网络问题

```bash
# 测试网络连通性
docker exec -it rag-api ping mongo
kubectl exec -it deployment/rag-api -- ping mongodb-service

# 端口检查
netstat -tlnp | grep :8000
kubectl port-forward service/rag-api 8000:8000 -n enterprise-rag
```

## 📞 技术支持

- **文档**: [项目Wiki](https://github.com/your-username/enterprise-rag-system/wiki)
- **问题反馈**: [GitHub Issues](https://github.com/your-username/enterprise-rag-system/issues)
- **社区讨论**: [GitHub Discussions](https://github.com/your-username/enterprise-rag-system/discussions)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。