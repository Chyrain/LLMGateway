"""
Coding Plan 管理路由 - CRUD 操作
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from config.database import SessionLocal
from models.coding_plan import CodingPlanConfig, CodingPlanUsage
from config.encryption import encrypt_api_key, decrypt_api_key

coding_plan_router = APIRouter()


# ==================== 请求模型 ====================
class CodingPlanCreate(BaseModel):
    """创建 Coding Plan 请求"""

    vendor: str
    vendor_name: Optional[str] = None
    package_type: str
    package_name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_first_month: Optional[float] = None
    quota_limits: Optional[Dict] = None
    quota_unit: Optional[str] = "requests"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    supported_models: Optional[List[str]] = None
    quota_query_method: Optional[str] = "控制台查看"
    quota_query_endpoint: Optional[str] = None
    quota_response_field: Optional[str] = None
    total_quota: Optional[int] = None
    expire_time: Optional[datetime] = None
    notes: Optional[str] = None


class CodingPlanUpdate(BaseModel):
    """更新 Coding Plan 请求"""

    vendor_name: Optional[str] = None
    package_type: Optional[str] = None
    package_name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_first_month: Optional[float] = None
    quota_limits: Optional[Dict] = None
    quota_unit: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    supported_models: Optional[List[str]] = None
    quota_query_method: Optional[str] = None
    quota_query_endpoint: Optional[str] = None
    quota_response_field: Optional[str] = None
    current_quota: Optional[int] = None
    total_quota: Optional[int] = None
    status: Optional[int] = None
    is_default: Optional[int] = None
    expire_time: Optional[datetime] = None
    notes: Optional[str] = None


# ==================== API 端点 ====================


@coding_plan_router.get("/api/coding-plans/configs")
async def list_coding_plan_configs():
    """获取所有 Coding Plan 配置"""
    db = SessionLocal()
    try:
        configs = db.query(CodingPlanConfig).all()
        return {"code": 200, "msg": "success", "data": [c.to_dict() for c in configs]}
    finally:
        db.close()


@coding_plan_router.get("/api/coding-plans/configs/{config_id}")
async def get_coding_plan_config(config_id: int):
    """获取单个 Coding Plan 配置"""
    db = SessionLocal()
    try:
        config = (
            db.query(CodingPlanConfig).filter(CodingPlanConfig.id == config_id).first()
        )
        if not config:
            return {"code": 404, "msg": "配置不存在", "data": None}

        return {
            "code": 200,
            "msg": "success",
            "data": config.to_dict(include_sensitive=True),
        }
    finally:
        db.close()


@coding_plan_router.post("/api/coding-plans/configs")
async def create_coding_plan_config(request: CodingPlanCreate):
    """创建 Coding Plan 配置"""
    db = SessionLocal()
    try:
        # 创建配置
        config = CodingPlanConfig(
            vendor=request.vendor,
            vendor_name=request.vendor_name,
            package_type=request.package_type,
            package_name=request.package_name,
            price_monthly=request.price_monthly,
            price_first_month=request.price_first_month,
            quota_limits=request.quota_limits,
            quota_unit=request.quota_unit,
            api_base=request.api_base,
            supported_models=request.supported_models,
            quota_query_method=request.quota_query_method,
            quota_query_endpoint=request.quota_query_endpoint,
            quota_response_field=request.quota_response_field,
            total_quota=request.total_quota,
            current_quota=request.total_quota,  # 初始剩余=总量
            expire_time=request.expire_time,
            notes=request.notes,
        )

        # 加密 API Key
        if request.api_key:
            config.api_key = encrypt_api_key(request.api_key)

        db.add(config)
        db.commit()
        db.refresh(config)

        return {"code": 200, "msg": "创建成功", "data": config.to_dict()}
    except Exception as e:
        db.rollback()
        return {"code": 500, "msg": f"创建失败: {str(e)}", "data": None}
    finally:
        db.close()


@coding_plan_router.put("/api/coding-plans/configs/{config_id}")
async def update_coding_plan_config(config_id: int, request: CodingPlanUpdate):
    """更新 Coding Plan 配置"""
    db = SessionLocal()
    try:
        config = (
            db.query(CodingPlanConfig).filter(CodingPlanConfig.id == config_id).first()
        )
        if not config:
            return {"code": 404, "msg": "配置不存在", "data": None}

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)

        # 特殊处理 API Key
        if "api_key" in update_data and update_data["api_key"]:
            update_data["api_key"] = encrypt_api_key(update_data["api_key"])

        for key, value in update_data.items():
            setattr(config, key, value)

        config.update_time = datetime.now()
        db.commit()
        db.refresh(config)

        return {"code": 200, "msg": "更新成功", "data": config.to_dict()}
    except Exception as e:
        db.rollback()
        return {"code": 500, "msg": f"更新失败: {str(e)}", "data": None}
    finally:
        db.close()


@coding_plan_router.delete("/api/coding-plans/configs/{config_id}")
async def delete_coding_plan_config(config_id: int):
    """删除 Coding Plan 配置"""
    db = SessionLocal()
    try:
        config = (
            db.query(CodingPlanConfig).filter(CodingPlanConfig.id == config_id).first()
        )
        if not config:
            return {"code": 404, "msg": "配置不存在", "data": None}

        db.delete(config)
        db.commit()

        return {"code": 200, "msg": "删除成功", "data": None}
    except Exception as e:
        db.rollback()
        return {"code": 500, "msg": f"删除失败: {str(e)}", "data": None}
    finally:
        db.close()


@coding_plan_router.post("/api/coding-plans/configs/{config_id}/set-default")
async def set_default_coding_plan(config_id: int):
    """设置默认 Coding Plan"""
    db = SessionLocal()
    try:
        # 先清除所有默认
        db.query(CodingPlanConfig).update({"is_default": 0})

        # 设置新的默认
        config = (
            db.query(CodingPlanConfig).filter(CodingPlanConfig.id == config_id).first()
        )
        if not config:
            return {"code": 404, "msg": "配置不存在", "data": None}

        config.is_default = 1
        db.commit()

        return {"code": 200, "msg": "设置成功", "data": config.to_dict()}
    except Exception as e:
        db.rollback()
        return {"code": 500, "msg": f"设置失败: {str(e)}", "data": None}
    finally:
        db.close()


# ==================== 使用记录 ====================


@coding_plan_router.get("/api/coding-plans/usage")
async def list_coding_plan_usage(plan_id: Optional[int] = None, limit: int = 100):
    """获取使用记录"""
    db = SessionLocal()
    try:
        query = db.query(CodingPlanUsage)

        if plan_id:
            query = query.filter(CodingPlanUsage.plan_id == plan_id)

        records = query.order_by(CodingPlanUsage.create_time.desc()).limit(limit).all()

        return {"code": 200, "msg": "success", "data": [r.to_dict() for r in records]}
    finally:
        db.close()
