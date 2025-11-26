"""
认证服务

处理用户认证和权限管理。
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

from ..utils.logger import get_logger
from ..models.schemas import User, UserRole

logger = get_logger(__name__)
security = HTTPBearer()

# 简化配置（生产环境应该从配置文件读取）
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class AuthService:
    """认证服务类"""

    def __init__(self):
        # 临时用户存储（生产环境应该使用数据库）
        self.users = {
            "admin": User(
                id="user_1",
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                hashed_password="hashed_admin_password",  # 实际应该加密
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        }

    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        try:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
            payload = {
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
                "exp": expire
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            logger.info(f"创建访问令牌成功: {user.username}")
            return token

        except Exception as e:
            logger.error(f"创建访问令牌失败: {e}")
            raise

    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token已过期")
        except jwt.JWTError as e:
            raise HTTPException(status_code=401, detail=f"Token无效: {str(e)}")

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        try:
            user = self.users.get(username)
            if not user:
                logger.warning(f"用户不存在: {username}")
                return None

            # 简化的密码验证（生产环境应该使用加密哈希）
            if password == "admin123" and username == "admin":
                user.last_login = datetime.utcnow()
                user.login_count += 1
                logger.info(f"用户认证成功: {username}")
                return user

            logger.warning(f"用户认证失败: {username}")
            return None

        except Exception as e:
            logger.error(f"用户认证异常: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.users.get(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

    def create_user(self, username: str, email: str, password: str, **kwargs) -> User:
        """创建新用户"""
        try:
            if username in self.users:
                raise ValueError(f"用户名已存在: {username}")

            user_id = f"user_{len(self.users) + 1}"
            user = User(
                id=user_id,
                username=username,
                email=email,
                hashed_password=f"hashed_{password}",  # 实际应该加密
                role=kwargs.get("role", UserRole.VIEWER),
                full_name=kwargs.get("full_name", ""),
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.users[username] = user
            logger.info(f"创建用户成功: {username}")
            return user

        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise

    def update_user(self, username: str, updates: Dict[str, Any]) -> Optional[User]:
        """更新用户信息"""
        try:
            user = self.users.get(username)
            if not user:
                return None

            for key, value in updates.items():
                if hasattr(user, key) and key != "id":  # 不允许修改ID
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            logger.info(f"更新用户成功: {username}")
            return user

        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            raise

    def check_permission(self, user: User, permission: str) -> bool:
        """检查用户权限"""
        try:
            # 管理员拥有所有权限
            if user.role == UserRole.ADMIN:
                return True

            # 检查用户特定权限
            return permission in user.permissions

        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False


# 全局认证服务实例
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户（依赖注入）"""
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token)

        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的令牌")

        user = auth_service.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="用户已禁用")

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {e}")
        raise HTTPException(status_code=401, detail="认证失败")


def require_permission(permission: str):
    """权限装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=403, detail="缺少用户信息")

            if not auth_service.check_permission(current_user, permission):
                raise HTTPException(status_code=403, detail=f"缺少权限: {permission}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: UserRole):
    """角色装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=403, detail="缺少用户信息")

            # 管理员可以访问所有资源
            if current_user.role == UserRole.ADMIN:
                return await func(*args, **kwargs)

            # 检查角色等级
            role_levels = {
                UserRole.VIEWER: 1,
                UserRole.KNOWLEDGE_WORKER: 2,
                UserRole.KNOWLEDGE_MANAGER: 3,
                UserRole.ADMIN: 4
            }

            if role_levels.get(current_user.role, 0) < role_levels.get(required_role, 999):
                raise HTTPException(status_code=403, detail=f"需要{required_role.value}角色")

            return await func(*args, **kwargs)
        return wrapper
    return decorator