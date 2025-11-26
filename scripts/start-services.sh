#!/bin/bash

# 企业级RAG知识库系统 - 服务组件启动脚本
# 用于启动开发环境所需的数据库和服务组件

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
企业级RAG知识库系统 - 服务组件启动脚本

用法:
    ./start-services.sh [选项] [模式]

模式:
    core            启动核心服务 (MongoDB + Redis + Qdrant)
    full            启动完整服务 (包含Elasticsearch, Neo4j, MinIO)
    stop            停止所有服务
    restart         重启服务
    status          查看服务状态
    logs            查看服务日志

选项:
    -h, --help      显示帮助信息
    -q, --quiet     静默模式
    -d, --detach    后台运行

示例:
    ./start-services.sh core          # 启动核心服务
    ./start-services.sh full -d       # 后台启动完整服务
    ./start-services.sh stop          # 停止所有服务
    ./start-services.sh logs mongodb  # 查看MongoDB日志

EOF
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker服务未启动，请启动Docker"
        exit 1
    fi

    log_info "Docker环境检查通过"
}

# 启动核心服务
start_core_services() {
    log_info "启动核心服务 (MongoDB + Redis + Qdrant)..."

    docker-compose -f docker-compose.dev.yml up $DOCKER_FLAGS \
        mongodb redis qdrant

    if [[ "$DETACH" == "true" ]]; then
        log_success "核心服务已在后台启动"
        show_service_info "core"
    fi
}

# 启动完整服务
start_full_services() {
    log_info "启动完整服务 (所有组件)..."

    docker-compose -f docker-compose.dev.yml up $DOCKER_FLAGS

    if [[ "$DETACH" == "true" ]]; then
        log_success "完整服务已在后台启动"
        show_service_info "full"
    fi
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    docker-compose -f docker-compose.dev.yml down
    log_success "所有服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker-compose -f docker-compose.dev.yml restart
    log_success "服务重启完成"
}

# 查看服务状态
show_status() {
    log_info "服务状态："
    docker-compose -f docker-compose.dev.yml ps
    echo

    log_info "健康检查："
    check_service_health
}

# 查看日志
show_logs() {
    local service=$1
    if [[ -z "$service" ]]; then
        docker-compose -f docker-compose.dev.yml logs -f
    else
        docker-compose -f docker-compose.dev.yml logs -f "$service"
    fi
}

# 检查服务健康状态
check_service_health() {
    local services=("mongodb:27017" "redis:6379" "qdrant:6333")

    for service in "${services[@]}"; do
        local name=${service%%:*}
        local port=${service##*:}

        if nc -z localhost "$port" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $name (localhost:$port)"
        else
            echo -e "  ${RED}✗${NC} $name (localhost:$port)"
        fi
    done
}

# 显示服务信息
show_service_info() {
    local mode=$1

    echo
    echo -e "${GREEN}=== 服务访问信息 ===${NC}"
    echo -e "MongoDB:        localhost:27017 (admin/password123)"
    echo -e "Redis:          localhost:6379 (password: password123)"
    echo -e "Qdrant:         localhost:6333"
    echo -e "Qdrant Web UI:  http://localhost:6333/dashboard"

    if [[ "$mode" == "full" ]]; then
        echo -e "Elasticsearch:  localhost:9200"
        echo -e "Neo4j Browser:  http://localhost:7474 (neo4j/password123)"
        echo -e "MinIO Console:  http://localhost:9001 (admin/password123)"
    fi

    echo
    echo -e "${BLUE}管理命令:${NC}"
    echo -e "  查看状态: ./start-services.sh status"
    echo -e "  查看日志: ./start-services.sh logs [服务名]"
    echo -e "  停止服务: ./start-services.sh stop"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务启动..."

    local services=("mongodb:27017" "redis:6379" "qdrant:6333")
    local max_wait=60
    local wait_time=0

    for service in "${services[@]}"; do
        local name=${service%%:*}
        local port=${service##*:}

        log_info "等待 $name 启动..."
        while ! nc -z localhost "$port" 2>/dev/null; do
            if [[ $wait_time -ge $max_wait ]]; then
                log_error "$name 启动超时"
                return 1
            fi

            sleep 2
            ((wait_time+=2))
        done

        log_success "$name 已启动"
    done

    log_success "所有核心服务已就绪"
}

# 主函数
main() {
    # 默认参数
    MODE=""
    DETACH="false"
    QUIET="false"
    DOCKER_FLAGS=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--detach)
                DETACH="true"
                DOCKER_FLAGS="-d"
                shift
                ;;
            -q|--quiet)
                QUIET="true"
                shift
                ;;
            core|full|stop|restart|status|logs)
                MODE="$1"
                shift
                ;;
            *)
                if [[ "$MODE" == "logs" ]]; then
                    SERVICE_NAME="$1"
                    shift
                else
                    log_error "未知参数: $1"
                    show_help
                    exit 1
                fi
                ;;
        esac
    done

    # 检查模式
    if [[ -z "$MODE" ]]; then
        log_error "请指定模式"
        show_help
        exit 1
    fi

    # 显示配置信息
    if [[ "$QUIET" != "true" ]]; then
        echo "=== 企业级RAG知识库系统 - 服务启动 ==="
        echo "模式: $MODE"
        echo "后台运行: $DETACH"
        echo "========================================="
        echo
    fi

    # 检查Docker环境
    check_docker

    # 执行操作
    case $MODE in
        core)
            start_core_services
            if [[ "$DETACH" == "true" ]]; then
                sleep 5
                wait_for_services
            fi
            ;;
        full)
            start_full_services
            if [[ "$DETACH" == "true" ]]; then
                sleep 10
                wait_for_services
            fi
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$SERVICE_NAME"
            ;;
        *)
            log_error "不支持的模式: $MODE"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"