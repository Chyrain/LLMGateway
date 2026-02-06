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
    email: Optional[str] = None
    phone: Optional[str] = None
    createdAt: Optional[str] = None

# 用户数据存储（生产环境应使用数据库）
users = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "createdAt": "2024-01-01 00:00:00"
    }
}

@auth_router.post("/api/auth/login")
async def login(
    username: str = Header(...),
    password: str = Header(...)
):
    """
    用户登录
    - 默认管理员: admin / admin123
    """
    if username not in users or users[username]["password"] != password:
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
    
    # 返回统一格式
    return {
        "code": 200,
        "msg": "登录成功",
        "data": {
            "access_token": token,
            "username": username
        }
    }

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

@auth_router.post("/api/auth/change-password")
async def change_password(
    old_password: str = Header(...),
    new_password: str = Header(...),
    authorization: str = Header(...)
):
    """
    修改密码
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token_key = authorization[7:]
    if token_key not in tokens:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    username = tokens[token_key]["username"]
    
    # 验证旧密码
    if users[username]["password"] != old_password:
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    # 更新密码
    users[username]["password"] = new_password
    
    return {"code": 200, "msg": "密码修改成功"}
