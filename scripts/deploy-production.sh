#!/bin/bash

# 企业级RAG知识库系统 - 生产环境部署脚本
# 支持Docker、Kubernetes多种部署方式

set -e

# 颜色输出
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

# 显示帮助
show_help() {
    cat << EOF
企业级RAG知识库系统 - 生产环境部署脚本

用法:
    ./deploy-production.sh [选项] [部署模式]

部署模式:
    docker          Docker Compose部署（默认）
    k8s             Kubernetes部署
    standalone      单机部署

选项:
    -e, --env       环境配置文件路径（默认: .env.production）
    -d, --domain    域名（用于SSL证书）
    -s, --ssl       启用SSL（需要提供域名）
    --backup        部署前备份现有数据
    --monitoring    启用监控（Prometheus + Grafana）
    --scale         扩展副本数量（格式：service=replicas）
    -h, --help      显示帮助信息

示例:
    ./deploy-production.sh docker
    ./deploy-production.sh docker --ssl -d your-domain.com
    ./deploy-production.sh k8s --monitoring --scale rag-api=3
    ./deploy-production.sh standalone --backup

EOF
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    local missing_deps=()

    # Docker相关
    if [[ "$DEPLOY_MODE" == "docker" ]]; then
        if ! command -v docker &> /dev/null; then
            missing_deps+=("docker")
        fi

        if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
            missing_deps+=("docker-compose")
        fi
    fi

    # Kubernetes相关
    if [[ "$DEPLOY_MODE" == "k8s" ]]; then
        if ! command -v kubectl &> /dev/null; then
            missing_deps+=("kubectl")
        fi

        if ! command -v helm &> /dev/null; then
            missing_deps+=("helm")
        fi
    fi

    # 通用工具
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        log_info "请先安装缺少的依赖，然后重新运行部署脚本"
        exit 1
    fi

    log_success "系统依赖检查完成"
}

# 准备环境配置
prepare_environment() {
    log_info "准备环境配置..."

    # 检查环境文件
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "环境文件 $ENV_FILE 不存在，创建默认配置"
        create_default_env
    fi

    # 加载环境变量
    set -a
    source "$ENV_FILE"
    set +a

    # 创建必要目录
    mkdir -p logs storage config monitoring/{prometheus,grafana} nginx/ssl

    log_success "环境配置准备完成"
}

# 创建默认环境配置
create_default_env() {
    cat > "$ENV_FILE" << 'EOF'
# 生产环境配置
ENVIRONMENT=production

# 数据库配置
MONGODB_HOST=mongo
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123
MONGODB_DATABASE=rag_kb

NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

QDRANT_HOST=qdrant
QDRANT_PORT=6333

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=password123

ELASTICSEARCH_HOSTS=elasticsearch:9200

# 对象存储
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123

# LLM配置
LLM_PROVIDER=anthropic
ANTHROPIC_AUTH_TOKEN=your_api_key_here
ANTHROPIC_BEDROCK_BASE_URL=https://ai-router.anker-in.com/bedrock
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 应用配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# 监控配置
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=admin123

# SSL配置
SSL_ENABLED=false
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
EOF

    log_warning "请编辑 $ENV_FILE 文件，配置您的实际参数"
}

# Docker部署
deploy_docker() {
    log_info "开始Docker部署..."

    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build --no-cache

    # 启动服务
    log_info "启动服务..."
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
    else
        docker-compose up -d
    fi

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30

    # 健康检查
    check_health_docker

    log_success "Docker部署完成"
}

# Kubernetes部署
deploy_k8s() {
    log_info "开始Kubernetes部署..."

    # 创建命名空间
    kubectl create namespace enterprise-rag --dry-run=client -o yaml | kubectl apply -f -

    # 部署配置文件
    kubectl apply -f k8s/ -n enterprise-rag

    # 等待部署完成
    log_info "等待Pod启动..."
    kubectl wait --for=condition=ready pod -l app=enterprise-rag -n enterprise-rag --timeout=300s

    # 健康检查
    check_health_k8s

    log_success "Kubernetes部署完成"
}

# 单机部署
deploy_standalone() {
    log_info "开始单机部署..."

    # 安装Python依赖
    pip3 install -r requirements.txt

    # 启动数据库服务（使用Docker）
    docker run -d --name rag-mongo -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=password123 \
        -v mongo_data:/data/db \
        mongo:6.0

    docker run -d --name rag-redis -p 6379:6379 \
        redis:7-alpine redis-server --requirepass password123

    # 启动应用
    nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &

    log_success "单机部署完成"
}

# Docker健康检查
check_health_docker() {
    log_info "执行健康检查..."

    local max_attempts=10
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:8000/health > /dev/null; then
            log_success "服务健康检查通过"
            return 0
        fi

        log_info "健康检查失败，重试中... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_error "服务健康检查失败"
    return 1
}

# Kubernetes健康检查
check_health_k8s() {
    log_info "执行健康检查..."

    local service_url=$(kubectl get service enterprise-rag-api -n enterprise-rag -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -z "$service_url" ]]; then
        service_url="localhost"
        kubectl port-forward service/enterprise-rag-api 8000:8000 -n enterprise-rag &
        sleep 5
    fi

    if curl -s "http://$service_url:8000/health" > /dev/null; then
        log_success "服务健康检查通过"
    else
        log_error "服务健康检查失败"
        return 1
    fi
}

# SSL配置
setup_ssl() {
    if [[ -z "$DOMAIN" ]]; then
        log_error "启用SSL需要指定域名"
        exit 1
    fi

    log_info "配置SSL证书..."

    # 使用Let's Encrypt生成证书
    docker run --rm -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
        certbot/certbot certonly --standalone \
        --email admin@${DOMAIN} \
        --agree-tos \
        --no-eff-email \
        -d ${DOMAIN}

    # 复制证书
    cp "nginx/ssl/live/${DOMAIN}/fullchain.pem" nginx/ssl/cert.pem
    cp "nginx/ssl/live/${DOMAIN}/privkey.pem" nginx/ssl/key.pem

    log_success "SSL证书配置完成"
}

# 数据备份
backup_data() {
    if [[ "$BACKUP_ENABLED" != "true" ]]; then
        return 0
    fi

    log_info "备份现有数据..."

    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # 备份MongoDB
    if docker ps | grep -q mongo; then
        docker exec enterprise-rag-mongo mongodump --out /tmp/backup
        docker cp enterprise-rag-mongo:/tmp/backup "$backup_dir/mongodb"
    fi

    # 备份向量数据
    if [[ -d "qdrant_data" ]]; then
        cp -r qdrant_data "$backup_dir/"
    fi

    log_success "数据备份完成: $backup_dir"
}

# 显示部署结果
show_deployment_info() {
    log_success "=== 部署完成 ==="

    case $DEPLOY_MODE in
        docker)
            echo -e "${GREEN}访问地址:${NC}"
            echo "  主页: http://localhost"
            echo "  API: http://localhost:8000"
            echo "  监控: http://localhost:3001 (Grafana)"
            echo "  API文档: http://localhost:8000/docs"
            ;;
        k8s)
            echo -e "${GREEN}Kubernetes服务信息:${NC}"
            kubectl get services -n enterprise-rag
            ;;
        standalone)
            echo -e "${GREEN}访问地址:${NC}"
            echo "  API: http://localhost:8000"
            echo "  健康检查: http://localhost:8000/health"
            ;;
    esac

    echo -e "\n${BLUE}管理命令:${NC}"
    case $DEPLOY_MODE in
        docker)
            echo "  查看日志: docker-compose logs -f"
            echo "  重启服务: docker-compose restart"
            echo "  停止服务: docker-compose down"
            ;;
        k8s)
            echo "  查看日志: kubectl logs -f deployment/enterprise-rag-api -n enterprise-rag"
            echo "  扩展服务: kubectl scale deployment enterprise-rag-api --replicas=3 -n enterprise-rag"
            echo "  删除服务: kubectl delete namespace enterprise-rag"
            ;;
        standalone)
            echo "  查看进程: ps aux | grep uvicorn"
            echo "  停止服务: pkill -f uvicorn"
            ;;
    esac
}

# 主函数
main() {
    # 默认参数
    DEPLOY_MODE="docker"
    ENV_FILE=".env.production"
    DOMAIN=""
    SSL_ENABLED="false"
    BACKUP_ENABLED="false"
    ENABLE_MONITORING="false"
    SCALE_SERVICES=()

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -s|--ssl)
                SSL_ENABLED="true"
                shift
                ;;
            --backup)
                BACKUP_ENABLED="true"
                shift
                ;;
            --monitoring)
                ENABLE_MONITORING="true"
                shift
                ;;
            --scale)
                SCALE_SERVICES+=("$2")
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            docker|k8s|standalone)
                DEPLOY_MODE="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示配置信息
    echo "=== 企业级RAG知识库系统 - 生产环境部署 ==="
    echo "部署模式: $DEPLOY_MODE"
    echo "环境文件: $ENV_FILE"
    echo "SSL启用: $SSL_ENABLED"
    echo "备份启用: $BACKUP_ENABLED"
    echo "监控启用: $ENABLE_MONITORING"
    echo "========================================="
    echo

    # 执行部署
    check_dependencies
    prepare_environment
    backup_data

    if [[ "$SSL_ENABLED" == "true" ]]; then
        setup_ssl
    fi

    case $DEPLOY_MODE in
        docker)
            deploy_docker
            ;;
        k8s)
            deploy_k8s
            ;;
        standalone)
            deploy_standalone
            ;;
        *)
            log_error "不支持的部署模式: $DEPLOY_MODE"
            exit 1
            ;;
    esac

    show_deployment_info
}

# 执行主函数
main "$@"