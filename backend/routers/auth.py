"""
认证 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import secrets
from sqlalchemy.orm import Session
from config.database import get_db

auth_router = APIRouter()

# 简单用户配置
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # 生产环境应该使用加密存储

# Token 存储 (生产环境应该使用 Redis)
tokens = {}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserInfo(BaseModel):
    username: str
    role: str = "admin"

@auth_router.post("/api/auth/login", response_model=TokenResponse)
async def login(
    username: str = Header(...),
    password: str = Header(...)
):
    """
    用户登录
    - 默认管理员: admin / admin123
    """
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 生成 token
    token = secrets.token_urlsafe(32)
    tokens[token] = {
        "username": username,
        "created_at": datetime.now()
    }
    
    return TokenResponse(
        access_token=token,
        username=username
    )

@auth_router.post("/api/auth/logout")
async def logout(
    authorization: str = Header(...)
):
    """
    用户登出
    """
    if authorization and authorization.startswith("Bearer "):
        token_key = authorization[7:]
        if token_key in tokens:
            del tokens[token_key]
    
    return {"code": 200, "msg": "登出成功"}

@auth_router.get("/api/auth/profile", response_model=UserInfo)
async def get_profile(
    authorization: str = Header(...)
):
    """
    获取当前用户信息
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token_key = authorization[7:]
    if token_key not in tokens:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    return UserInfo(username=tokens[token_key]["username"])
