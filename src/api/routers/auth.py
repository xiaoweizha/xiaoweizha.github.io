"""
认证路由

用户认证和授权相关接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import time
import jwt
from typing import Optional

from ...utils.logger import get_logger
from ...utils.config import get_config

router = APIRouter()
logger = get_logger(__name__)
config = get_config()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """用户信息"""
    username: str
    roles: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    try:
        # 简化的认证逻辑 (生产环境需要连接真实的用户数据库)
        if request.username == "admin" and request.password == "admin123":
            # 生成JWT token
            payload = {
                "sub": request.username,
                "roles": ["admin"],
                "exp": int(time.time()) + 3600 * 24  # 24小时过期
            }

            token = jwt.encode(payload, "secret_key", algorithm="HS256")

            return LoginResponse(
                access_token=token,
                expires_in=3600 * 24
            )
        else:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

    except Exception as e:
        logger.error("登录失败", error=str(e))
        raise HTTPException(status_code=500, detail="登录服务异常")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """获取当前用户"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])

        return UserInfo(
            username=payload["sub"],
            roles=payload.get("roles", [])
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token无效")


@router.get("/me", response_model=UserInfo)
async def get_user_info(current_user: UserInfo = Depends(get_current_user)):
    """获取用户信息"""
    return current_user


@router.post("/logout")
async def logout(current_user: UserInfo = Depends(get_current_user)):
    """用户登出"""
    return {"message": "登出成功"}