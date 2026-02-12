"""
系统配置 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from config.database import get_db
from models.system_config import SystemConfig

config_router = APIRouter()

# 内存配置存储（生产环境应使用数据库）
config_store = {
    "gateway_port": "8080",
    "gateway_api_key": "",
    "alert_threshold": "80",
    "switch_threshold": "99",
    "log_retention": "30",
    "refresh_interval": "60",
}


class ConfigSetRequest(BaseModel):
    key: str
    value: str


@config_router.get("/api/config/list")
async def list_configs(db: Session = Depends(get_db)):
    """
    获取所有配置（从数据库读取）
    """
    try:
        # 从数据库读取所有配置
        configs = db.query(SystemConfig).all()
        result = {}
        for config in configs:
            result[config.config_key] = config.config_value

        # 合并内存中的配置（作为默认值）
        for key, value in config_store.items():
            if key not in result:
                result[key] = value

        return {"code": 200, "msg": "success", "data": result}
    except Exception as e:
        print(f"从数据库读取配置失败: {e}")
        return {"code": 200, "msg": "success", "data": config_store}


@config_router.get("/api/config/{key}")
async def get_config(key: str):
    """
    获取单个配置
    """
    if key not in config_store:
        # 尝试从数据库获取
        return {
            "code": 200,
            "msg": "success",
            "data": {"config_value": config_store.get(key, "")},
        }

    return {
        "code": 200,
        "msg": "success",
        "data": {"config_value": config_store.get(key, "")},
    }


@config_router.post("/api/config/set")
async def set_config(request: ConfigSetRequest, db: Session = Depends(get_db)):
    """
    设置配置
    """
    config_store[request.key] = request.value

    # 保存到数据库
    try:
        existing = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == request.key)
            .first()
        )
        if existing:
            existing.config_value = request.value
        else:
            config = SystemConfig(config_key=request.key, config_value=request.value)
            db.add(config)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"保存配置到数据库失败: {e}")

    return {"code": 200, "msg": "配置已更新"}


@config_router.post("/api/config/reset-encrypt-key")
async def reset_encrypt_key():
    """
    重置加密密钥
    """
    import secrets

    new_key = secrets.token_urlsafe(32)
    config_store["encrypt_key"] = new_key

    return {"code": 200, "msg": "加密密钥已重置"}
