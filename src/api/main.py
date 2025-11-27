"""
FastAPI主应用

企业级RAG知识库系统的API入口。
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import uuid
import structlog
import os
from pathlib import Path

from ..utils.config import get_config
from ..utils.logger import setup_logging, get_logger
from ..core.rag_engine import RAGEngine
from .routers import (
    auth_router,
    documents_router,
    chat_router,
    knowledge_base_router,
    admin_router,
    websocket_router
)

# 配置日志
config = get_config()
setup_logging(
    level=config.monitoring.log_level,
    format_type=config.monitoring.log_format,
    log_file=config.monitoring.log_file_path
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    logger.info("启动企业RAG知识库系统")

    # 初始化RAG引擎
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    app.state.rag_engine = rag_engine

    logger.info("RAG引擎初始化完成")

    yield

    # 清理资源
    logger.info("关闭企业RAG知识库系统")
    await rag_engine.close()


# 创建FastAPI应用
app = FastAPI(
    title="企业级RAG知识库系统",
    description="基于LightRAG的企业级检索增强生成知识库系统",
    version=config.system_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS中间件
cors_origins = config.security.cors_origins.split(",") if config.security.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 可信主机中间件
if not config.server.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.your-domain.com"]
    )


# 请求日志中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # 记录请求开始
    logger.info(
        "请求开始",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            "请求完成",
            request_id=request_id,
            status_code=response.status_code,
            process_time=process_time
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # 记录请求错误
        logger.error(
            "请求错误",
            request_id=request_id,
            error=str(e),
            process_time=process_time
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "内部服务器错误",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(
        "HTTP异常",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        "未捕获异常",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url)
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "内部服务器错误",
            "timestamp": time.time()
        }
    )


# 根路径 - 返回前端页面
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    try:
        # 获取前端文件路径
        current_dir = Path(__file__).parent.parent.parent
        frontend_file = current_dir / "frontend" / "index.html"

        if frontend_file.exists():
            return FileResponse(str(frontend_file))
        else:
            # 如果找不到前端文件，返回简单的HTML页面
            return HTMLResponse("""
            <html>
                <head><title>企业级RAG知识库系统</title></head>
                <body>
                    <h1>企业级RAG知识库系统</h1>
                    <p>系统正在运行中...</p>
                    <p><a href="/docs">查看API文档</a></p>
                    <p><a href="/health">系统健康检查</a></p>
                </body>
            </html>
            """)
    except Exception as e:
        logger.error("返回前端页面失败", error=str(e))
        return HTMLResponse("<h1>系统错误</h1><p>无法加载前端页面</p>")

# 系统信息API
@app.get("/api/system/info")
async def system_info_api():
    """系统信息API"""
    return {
        "name": config.system_name,
        "version": config.system_version,
        "status": "running",
        "docs_url": "/docs",
        "health_url": "/health"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        rag_engine = app.state.rag_engine
        health_result = await rag_engine.health_check()

        return {
            "status": health_result["status"],
            "timestamp": time.time(),
            "version": config.system_version,
            "components": health_result["components"]
        }

    except Exception as e:
        logger.error("健康检查失败", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# 系统信息
@app.get("/system/info")
async def system_info():
    """获取系统信息"""
    try:
        rag_engine = app.state.rag_engine
        stats = await rag_engine.get_statistics()

        return {
            "system": {
                "name": config.system_name,
                "version": config.system_version,
                "environment": config.server.environment
            },
            "statistics": stats,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error("获取系统信息失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统信息失败")


# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["文档管理"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["智能问答"])
app.include_router(knowledge_base_router, prefix="/api/v1/knowledge-bases", tags=["知识库"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["系统管理"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

logger.info("API路由注册完成")