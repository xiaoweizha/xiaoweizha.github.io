"""
API接口模块

提供RESTful API和WebSocket接口。
"""

from .main import app
from .routers import *

__all__ = ["app"]