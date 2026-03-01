"""
配额管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from config.database import get_db
from models.quota_stat import QuotaStat
from models.model_config import ModelConfig
from services.quota_monitor import QuotaMonitor

quota_router = APIRouter()


class QuotaSetRequest(BaseModel):
    """设置配额请求"""
    model_id: int
    total_quota: float
    plan_type: str = "default"
    plan_name: str = ""
    quota_unit: str = "tokens"  # tokens=Token数, prompts=请求次数
    period_hours: int = 0  # 周期小时数，0表示无周期限制


class QuotaBatchSetRequest(BaseModel):
    """批量设置配额请求"""
    quotas: List[QuotaSetRequest]


class QuotaUpdateRequest(BaseModel):
    """更新配额请求"""
    total_quota: Optional[float] = None
    plan_type: Optional[str] = None
    plan_name: Optional[str] = None


@quota_router.get("/api/quota/list")
async def list_quotas(db=Depends(get_db)):
    """
    获取所有模型的配额信息
    """
    try:
        quotas = QuotaMonitor.get_all_quotas()
        return {"code": 200, "msg": "success", "data": quotas}
    except Exception as e:
        print(f"[ERROR] 获取配额列表失败: {e}")
        return {"code": 500, "msg": f"获取配额列表失败: {str(e)}", "data": []}


@quota_router.get("/api/quota/history")
async def get_quota_history(model_id: Optional[int] = None, days: int = 30, db=Depends(get_db)):
    """
    获取额度历史记录
    """
    from datetime import timedelta

    history = []
    end_date = datetime.now()

    for i in range(days):
        date = end_date - timedelta(days=days - 1 - i)
        history.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "total": 1000000,
                "used": i * 10000 + 50000,
                "remain": 1000000 - i * 10000 - 50000,
                "usage_rate": round((i * 10000 + 50000) / 1000000 * 100, 2),
            }
        )

    return {"code": 200, "msg": "success", "data": history}


@quota_router.get("/api/quota/{model_id}")
async def get_quota(model_id: int, db=Depends(get_db)):
    """
    获取指定模型的配额信息
    """
    try:
        quota = QuotaMonitor.get_quota(model_id)
        if not quota:
            return {"code": 404, "msg": "配额记录不存在", "data": None}
        return {"code": 200, "msg": "success", "data": quota}
    except Exception as e:
        print(f"[ERROR] 获取配额失败: {e}")
        return {"code": 500, "msg": f"获取配额失败: {str(e)}", "data": None}


@quota_router.post("/api/quota/set")
async def set_quota(request: QuotaSetRequest, db=Depends(get_db)):
    """
    设置模型配额（手动）
    """
    try:
        # 验证模型是否存在
        model = db.query(ModelConfig).filter(ModelConfig.id == request.model_id).first()
        if not model:
            return {"code": 404, "msg": "模型不存在", "data": None}

        success = QuotaMonitor.set_quota(
            model_id=request.model_id,
            total_quota=request.total_quota,
            plan_type=request.plan_type,
            plan_name=request.plan_name,
            quota_unit=request.quota_unit,
            period_hours=request.period_hours
        )

        if success:
            return {"code": 200, "msg": "配额设置成功", "data": {
                "model_id": request.model_id,
                "total_quota": request.total_quota,
                "plan_type": request.plan_type,
                "plan_name": request.plan_name,
                "quota_unit": request.quota_unit,
                "period_hours": request.period_hours
            }}
        else:
            return {"code": 500, "msg": "配额设置失败", "data": None}
    except Exception as e:
        print(f"[ERROR] 设置配额失败: {e}")
        return {"code": 500, "msg": f"设置配额失败: {str(e)}", "data": None}


@quota_router.post("/api/quota/batch-set")
async def batch_set_quota(request: QuotaBatchSetRequest, db=Depends(get_db)):
    """
    批量设置模型配额
    """
    results = []
    for quota_req in request.quotas:
        model = db.query(ModelConfig).filter(ModelConfig.id == quota_req.model_id).first()
        if not model:
            results.append({
                "model_id": quota_req.model_id,
                "success": False,
                "msg": "模型不存在"
            })
            continue

        success = QuotaMonitor.set_quota(
            model_id=quota_req.model_id,
            total_quota=quota_req.total_quota,
            plan_type=quota_req.plan_type,
            plan_name=quota_req.plan_name
        )
        results.append({
            "model_id": quota_req.model_id,
            "success": success,
            "msg": "设置成功" if success else "设置失败"
        })

    return {"code": 200, "msg": "批量设置完成", "data": results}


@quota_router.put("/api/quota/{model_id}")
async def update_quota(model_id: int, request: QuotaUpdateRequest, db=Depends(get_db)):
    """
    更新模型配额
    """
    try:
        quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
        if not quota:
            return {"code": 404, "msg": "配额记录不存在", "data": None}

        # 更新字段
        if request.total_quota is not None:
            quota.total_quota = request.total_quota
            quota.remain_quota = request.total_quota - quota.used_quota
            quota.used_ratio = (quota.used_quota / request.total_quota * 100) if request.total_quota > 0 else 0

        if request.plan_type is not None:
            quota.plan_type = request.plan_type

        if request.plan_name is not None:
            quota.plan_name = request.plan_name

        db.commit()

        # 更新模型状态
        QuotaMonitor._update_model_quota_status(model_id, quota.used_ratio)

        return {"code": 200, "msg": "配额更新成功", "data": QuotaMonitor.get_quota(model_id)}
    except Exception as e:
        print(f"[ERROR] 更新配额失败: {e}")
        db.rollback()
        return {"code": 500, "msg": f"更新配额失败: {str(e)}", "data": None}


@quota_router.post("/api/quota/{model_id}/reset")
async def reset_quota(model_id: int, db=Depends(get_db)):
    """
    重置模型配额（用量清零）
    """
    try:
        success = QuotaMonitor.reset_quota(model_id)
        if success:
            return {"code": 200, "msg": "配额已重置", "data": QuotaMonitor.get_quota(model_id)}
        else:
            return {"code": 500, "msg": "重置配额失败", "data": None}
    except Exception as e:
        print(f"[ERROR] 重置配额失败: {e}")
        return {"code": 500, "msg": f"重置配额失败: {str(e)}", "data": None}


@quota_router.delete("/api/quota/{model_id}")
async def delete_quota(model_id: int, db=Depends(get_db)):
    """
    删除模型配额记录
    """
    try:
        success = QuotaMonitor.delete_quota(model_id)
        if success:
            return {"code": 200, "msg": "配额记录已删除", "data": None}
        else:
            return {"code": 500, "msg": "删除配额记录失败", "data": None}
    except Exception as e:
        print(f"[ERROR] 删除配额记录失败: {e}")
        return {"code": 500, "msg": f"删除配额记录失败: {str(e)}", "data": None}


@quota_router.post("/api/quota/{model_id}/add-usage")
async def add_usage(model_id: int, tokens: int, db=Depends(get_db)):
    """
    手动增加使用量
    """
    try:
        success = QuotaMonitor.add_usage(model_id, tokens)
        if success:
            return {"code": 200, "msg": "用量已添加", "data": QuotaMonitor.get_quota(model_id)}
        else:
            return {"code": 500, "msg": "添加用量失败", "data": None}
    except Exception as e:
        print(f"[ERROR] 添加用量失败: {e}")
        return {"code": 500, "msg": f"添加用量失败: {str(e)}", "data": None}


@quota_router.get("/api/quota-status/{model_id}")
async def get_quota_status(model_id: int, db=Depends(get_db)):
    """
    获取模型配额状态（0=已耗尽, 1=即将耗尽, 2=充足）
    """
    try:
        status = QuotaMonitor.get_quota_status(model_id)
        status_text = {0: "已耗尽", 1: "即将耗尽", 2: "充足"}.get(status, "未知")
        return {"code": 200, "msg": "success", "data": {
            "model_id": model_id,
            "status": status,
            "status_text": status_text
        }}
    except Exception as e:
        print(f"[ERROR] 获取配额状态失败: {e}")
        return {"code": 500, "msg": f"获取配额状态失败: {str(e)}", "data": None}
