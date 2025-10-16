"""认证中间件"""
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.user_service import user_service
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer安全方案
security = HTTPBearer()


async def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    强制认证中间件

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        用户信息

    Raises:
        HTTPException: 401 未认证
    """
    token = credentials.credentials

    user = user_service.find_user_by_token(token)

    if not user:
        logger.warning(f"Invalid token attempt: {token[:20]}...")
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌"
        )

    logger.debug(f"User authenticated: {user['username']}")
    return user


async def optional_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    可选认证中间件（不强制要求token）

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        用户信息或None
    """
    if not credentials:
        return None

    token = credentials.credentials
    user = user_service.find_user_by_token(token)

    if user:
        logger.debug(f"Optional auth: User {user['username']} authenticated")
    else:
        logger.debug("Optional auth: No valid user")

    return user
