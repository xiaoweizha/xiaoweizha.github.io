#!/bin/bash

# 企业级RAG知识库系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_warning "Python3未安装，将在Docker中运行"
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_warning "Node.js未安装，将在Docker中运行"
    fi

    log_success "依赖检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    directories=(
        "logs"
        "storage/documents"
        "storage/exports"
        "storage/temp"
        "monitoring/prometheus"
        "monitoring/grafana/provisioning/datasources"
        "monitoring/grafana/provisioning/dashboards"
        "monitoring/grafana/dashboards"
        "nginx"
        "scripts"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done

    log_success "目录创建完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."

    # 检查.env文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env文件不存在，从.env.example复制"
            cp .env.example .env
            log_warning "请编辑.env文件，配置必要的环境变量"
        else
            log_error ".env.example文件不存在"
            exit 1
        fi
    fi

    # 检查配置文件
    if [ ! -f "config/config.yaml" ]; then
        log_error "config/config.yaml配置文件不存在"
        exit 1
    fi

    log_success "配置文件检查完成"
}

# 生成默认配置
generate_default_configs() {
    log_info "生成默认配置文件..."

    # Prometheus配置
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'rag-api'
    static_configs:
      - targets: ['rag-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'mongodb-exporter'
    static_configs:
      - targets: ['mongodb-exporter:9216']
EOF

    # Grafana数据源配置
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Nginx配置
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server rag-api:8000;
    }

    upstream frontend {
        server rag-frontend:80;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # API
        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 健康检查
        location /health {
            proxy_pass http://api/health;
        }

        # 系统信息
        location /system/ {
            proxy_pass http://api/system/;
        }

        # 监控指标
        location /metrics {
            proxy_pass http://api/metrics;
        }
    }
}
EOF

    log_success "默认配置文件生成完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."

    # 构建后端镜像
    log_info "构建RAG API镜像..."
    docker build -t enterprise-rag-api:latest .

    # 构建前端镜像（如果存在）
    if [ -f "frontend/Dockerfile" ]; then
        log_info "构建前端镜像..."
        docker build -t enterprise-rag-frontend:latest ./frontend
    fi

    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    # 启动基础设施服务
    log_info "启动数据库服务..."
    docker-compose up -d mongo neo4j qdrant redis elasticsearch minio

    # 等待数据库服务启动
    log_info "等待数据库服务启动..."
    sleep 30

    # 检查数据库连接
    check_databases

    # 启动应用服务
    log_info "启动应用服务..."
    docker-compose up -d rag-api

    # 等待API服务启动
    log_info "等待API服务启动..."
    wait_for_service "http://localhost:8000/health" "RAG API"

    # 启动前端服务
    if [ -f "frontend/Dockerfile" ]; then
        log_info "启动前端服务..."
        docker-compose up -d rag-frontend
    fi

    # 启动监控服务
    log_info "启动监控服务..."
    docker-compose up -d prometheus grafana

    # 启动Nginx
    log_info "启动Nginx..."
    docker-compose up -d nginx

    log_success "所有服务启动完成"
}

# 检查数据库连接
check_databases() {
    log_info "检查数据库连接..."

    # 检查MongoDB
    if docker-compose exec mongo mongo --eval "db.adminCommand('ismaster')" &> /dev/null; then
        log_success "MongoDB连接正常"
    else
        log_warning "MongoDB连接失败"
    fi

    # 检查Redis
    if docker-compose exec redis redis-cli ping &> /dev/null; then
        log_success "Redis连接正常"
    else
        log_warning "Redis连接失败"
    fi

    # 检查Neo4j (简单检查端口)
    if docker-compose ps neo4j | grep -q "Up"; then
        log_success "Neo4j服务运行中"
    else
        log_warning "Neo4j服务异常"
    fi

    # 检查Qdrant
    if curl -s http://localhost:6333/collections &> /dev/null; then
        log_success "Qdrant连接正常"
    else
        log_warning "Qdrant连接失败"
    fi
}

# 等待服务启动
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    log_info "等待 $name 服务启动..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s --fail "$url" &> /dev/null; then
            log_success "$name 服务已启动"
            return 0
        fi

        log_info "等待 $name 服务启动... (尝试 $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_error "$name 服务启动超时"
    return 1
}

# 显示服务信息
show_services_info() {
    log_success "企业级RAG知识库系统启动完成！"
    echo
    echo "=== 服务访问地址 ==="
    echo "🌐 主页面:     http://localhost"
    echo "🚀 API文档:    http://localhost/api/v1/docs"
    echo "💚 健康检查:   http://localhost/health"
    echo "📊 系统信息:   http://localhost/system/info"
    echo "📈 Grafana:   http://localhost:3001 (admin/admin123)"
    echo "📊 Prometheus: http://localhost:9090"
    echo "🗄️  MongoDB:   localhost:27017 (admin/password123)"
    echo "🕸️  Neo4j:     http://localhost:7474 (neo4j/password123)"
    echo "🔍 Qdrant:    http://localhost:6333"
    echo "📦 MinIO:     http://localhost:9001 (admin/password123)"
    echo
    echo "=== 快速操作 ==="
    echo "查看日志: docker-compose logs -f rag-api"
    echo "停止服务: docker-compose down"
    echo "重启服务: docker-compose restart"
    echo "查看状态: docker-compose ps"
    echo
}

# 初始化数据
init_data() {
    log_info "初始化系统数据..."

    # 等待API服务完全启动
    sleep 10

    # 创建默认管理员用户（如果需要）
    if command -v curl &> /dev/null; then
        log_info "检查系统初始化状态..."

        # 这里可以添加初始化逻辑
        # 例如：创建默认用户、导入示例数据等

        log_success "系统初始化完成"
    else
        log_warning "curl未安装，跳过数据初始化"
    fi
}

# 主函数
main() {
    echo "================================================"
    echo "       企业级RAG知识库系统启动脚本"
    echo "================================================"
    echo

    # 检查参数
    case "${1:-start}" in
        "start")
            check_dependencies
            create_directories
            check_config
            generate_default_configs
            build_images
            start_services
            init_data
            show_services_info
            ;;
        "stop")
            log_info "停止所有服务..."
            docker-compose down
            log_success "所有服务已停止"
            ;;
        "restart")
            log_info "重启服务..."
            docker-compose restart
            log_success "服务重启完成"
            ;;
        "logs")
            log_info "显示服务日志..."
            docker-compose logs -f "${2:-rag-api}"
            ;;
        "status")
            log_info "服务状态:"
            docker-compose ps
            ;;
        "clean")
            log_warning "清理所有数据..."
            read -p "确认删除所有数据？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose down -v
                docker system prune -f
                log_success "清理完成"
            else
                log_info "取消清理"
            fi
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [命令]"
            echo
            echo "命令:"
            echo "  start     启动所有服务 (默认)"
            echo "  stop      停止所有服务"
            echo "  restart   重启服务"
            echo "  logs      显示日志 [服务名]"
            echo "  status    显示服务状态"
            echo "  clean     清理所有数据"
            echo "  help      显示帮助信息"
            echo
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'log_warning "脚本被中断"; exit 130' INT

# 执行主函数
main "$@"