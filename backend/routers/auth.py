"""
认证 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from config.database import get_db

auth_router = APIRouter()
security = HTTPBasic()

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
    credentials: HTTPBasicCredentials,
    db: Session = Depends(get_db)
):
    """
    用户登录
    - 默认管理员: admin / admin123
    """
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"}
        )
    
    # 生成 token
    token = secrets.token_urlsafe(32)
    tokens[token] = {
        "username": credentials.username,
        "created_at": datetime.now()
    }
    
    return TokenResponse(
        access_token=token,
        username=credentials.username
    )

@auth_router.post("/api/auth/logout")
async def logout(
    token: str = Security(HTTPBasic())
):
    """
    用户登出
    """
    # HTTP Basic auth 自动验证 token
    auth_header = token
    if auth_header and auth_header.startswith("Bearer "):
        token_key = auth_header[7:]
        if token_key in tokens:
            del tokens[token_key]
    
    return {"code": 200, "msg": "登出成功"}

@auth_router.get("/api/auth/profile", response_model=UserInfo)
async def get_profile(
    token: str = Security(HTTPBasic())
):
    """
    获取当前用户信息
    """
    auth_header = token
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token_key = auth_header[7:]
    if token_key not in tokens:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    return UserInfo(username=tokens[token_key]["username"])
