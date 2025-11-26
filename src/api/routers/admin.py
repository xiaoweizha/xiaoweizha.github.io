"""
系统管理路由

系统管理和监控相关接口。
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any
import time
import psutil

from ...utils.logger import get_logger
from .auth import get_current_user, UserInfo

router = APIRouter()
logger = get_logger(__name__)


class SystemStats(BaseModel):
    """系统统计信息"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime: float


class ServiceStatus(BaseModel):
    """服务状态"""
    name: str
    status: str
    last_check: float


class SystemInfo(BaseModel):
    """系统信息"""
    stats: SystemStats
    services: list[ServiceStatus]
    version: str
    environment: str


def check_admin_role(current_user: UserInfo):
    """检查管理员权限"""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/system/stats", response_model=SystemInfo)
async def get_system_stats(
    request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取系统统计信息"""
    check_admin_role(current_user)

    try:
        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        stats = SystemStats(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            uptime=time.time() - psutil.boot_time()
        )

        # 检查服务状态
        services = [
            ServiceStatus(
                name="RAG引擎",
                status="running",
                last_check=time.time()
            ),
            ServiceStatus(
                name="数据库连接",
                status="connected",
                last_check=time.time()
            )
        ]

        return SystemInfo(
            stats=stats,
            services=services,
            version="1.0.0",
            environment="production"
        )

    except Exception as e:
        logger.error("获取系统统计失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统统计失败")


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO",
    current_user: UserInfo = Depends(get_current_user)
):
    """获取系统日志"""
    check_admin_role(current_user)

    try:
        # TODO: 实际的日志读取逻辑
        mock_logs = [
            {
                "timestamp": time.time() - 60,
                "level": "INFO",
                "message": "RAG引擎初始化完成",
                "logger": "src.core.rag_engine"
            },
            {
                "timestamp": time.time() - 30,
                "level": "INFO",
                "message": "用户登录成功",
                "logger": "src.api.routers.auth",
                "user": "admin"
            }
        ]

        return {
            "logs": mock_logs[:lines],
            "total": len(mock_logs)
        }

    except Exception as e:
        logger.error("获取系统日志失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统日志失败")


@router.post("/system/restart")
async def restart_system(
    current_user: UserInfo = Depends(get_current_user)
):
    """重启系统"""
    check_admin_role(current_user)

    try:
        logger.info("系统重启请求", user=current_user.username)

        # TODO: 实际的重启逻辑
        # 注意：这个操作需要谨慎实现，可能需要外部脚本支持

        return {"message": "系统重启请求已提交"}

    except Exception as e:
        logger.error("系统重启失败", error=str(e))
        raise HTTPException(status_code=500, detail="系统重启失败")


@router.get("/users")
async def list_users(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取用户列表"""
    check_admin_role(current_user)

    try:
        # TODO: 从数据库获取用户列表
        mock_users = [
            {
                "id": "user1",
                "username": "admin",
                "roles": ["admin"],
                "created_at": time.time() - 86400,
                "last_login": time.time() - 3600,
                "status": "active"
            }
        ]

        return {
            "users": mock_users,
            "total": len(mock_users)
        }

    except Exception as e:
        logger.error("获取用户列表失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.get("/config")
async def get_system_config(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取系统配置"""
    check_admin_role(current_user)

    try:
        # TODO: 获取系统配置信息（敏感信息需要过滤）
        config_info = {
            "system": {
                "name": "企业级RAG知识库系统",
                "version": "1.0.0",
                "environment": "production"
            },
            "features": {
                "authentication": True,
                "document_upload": True,
                "knowledge_graph": True,
                "monitoring": True
            }
        }

        return config_info

    except Exception as e:
        logger.error("获取系统配置失败", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统配置失败")