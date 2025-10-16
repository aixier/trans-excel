"""认证API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.user_service import user_service
from middleware.auth import require_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: dict


@router.post("/login")
async def login(request: LoginRequest):
    """
    用户登录

    Args:
        request: 登录请求（用户名+密码）

    Returns:
        登录响应（token+用户信息）
    """
    try:
        # 参数验证
        if not request.username or not request.password:
            raise HTTPException(
                status_code=400,
                detail="用户名和密码不能为空"
            )

        # 验证用户凭据
        user = user_service.authenticate(request.username, request.password)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="用户名或密码错误"
            )

        logger.info(f"User logged in: {request.username}")

        return {
            "code": 200,
            "success": True,
            "data": {
                "token": user['token'],
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "displayName": user['displayName'],
                    "email": user['email'],
                    "role": user.get('role', 'user')
                }
            },
            "message": "登录成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="登录服务错误"
        )


@router.get("/verify")
async def verify_token(user: dict = require_auth):
    """
    验证token

    Args:
        user: 当前用户（由中间件注入）

    Returns:
        Token验证结果
    """
    return {
        "code": 200,
        "success": True,
        "data": {
            "valid": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "displayName": user['displayName'],
                "email": user['email'],
                "role": user.get('role', 'user')
            }
        },
        "message": "Token有效"
    }


@router.get("/users")
async def get_users(user: dict = require_auth):
    """
    获取用户列表（需要管理员权限）

    Args:
        user: 当前用户（由中间件注入）

    Returns:
        用户列表
    """
    # 检查权限
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )

    try:
        users = user_service.get_all_users()

        return {
            "code": 200,
            "success": True,
            "data": {"users": users},
            "message": "获取用户列表成功"
        }

    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取用户列表失败"
        )


@router.post("/logout")
async def logout(user: dict = require_auth):
    """
    用户登出（演示用，实际只是返回成功）

    Args:
        user: 当前用户

    Returns:
        登出结果
    """
    logger.info(f"User logged out: {user['username']}")

    return {
        "code": 200,
        "success": True,
        "message": "登出成功"
    }
