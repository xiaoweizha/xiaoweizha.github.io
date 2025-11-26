"""
API路由模块

包含所有API路由定义。
"""

from .auth import router as auth_router
from .documents import router as documents_router
from .chat import router as chat_router
from .knowledge_base import router as knowledge_base_router
from .admin import router as admin_router
from .websocket import router as websocket_router

__all__ = [
    "auth_router",
    "documents_router",
    "chat_router",
    "knowledge_base_router",
    "admin_router",
    "websocket_router"
]