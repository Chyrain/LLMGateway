"""
统计 API 路由
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from config.database import get_db
from models.model_config import ModelConfig
from models.quota_stat import QuotaStat
from models.operation_log import OperationLog
from models.notification import Notification
from models.system_config import SystemConfig

stats_router = APIRouter()


class DashboardStats(BaseModel):
    totalRequests: int
    activeModels: int
    totalQuota: float
    switchCount: int


class ModelRanking(BaseModel):
    model: str
    requests: int
    percentage: float


class UsageTrend(BaseModel):
    date: str
    requests: int


class DashboardResponse(BaseModel):
    code: int
    msg: str
    data: dict


@stats_router.get("/api/stats/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    获取仪表盘统计数据
    """
    # 活跃模型数量
    active_models = (
        db.query(ModelConfig)
        .filter(ModelConfig.status == 1, ModelConfig.connect_status == 1)
        .count()
    )

    # 今日切换次数
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    switch_count = (
        db.query(func.count(OperationLog.id))
        .filter(
            OperationLog.log_type == 2,  # 切换类型
            OperationLog.create_time >= today,
        )
        .scalar()
        or 0
    )

    # 今日请求次数
    today_requests = (
        db.query(func.count(OperationLog.id))
        .filter(
            OperationLog.log_type == 1,  # 请求类型
            OperationLog.create_time >= today,
        )
        .scalar()
        or 0
    )

    # 统计额度
    quota_stats = db.query(QuotaStat).all()
    total_quota = sum(s.total_quota for s in quota_stats)
    used_quota = sum(s.used_quota for s in quota_stats)

    # 当前使用模型
    current_model = (
        db.query(ModelConfig)
        .filter(ModelConfig.status == 1)
        .order_by(ModelConfig.priority)
        .first()
    )

    current_quota = None
    if current_model:
        current_quota = (
            db.query(QuotaStat).filter(QuotaStat.model_id == current_model.id).first()
        )

    # 额度预警模型
    # 从配置中获取阈值，默认为80%
    threshold = 80
    try:
        threshold_config = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == "alert_threshold")
            .first()
        )
        if threshold_config and threshold_config.config_value:
            threshold = int(threshold_config.config_value)
    except Exception:
        pass

    alert_models = []
    for qs in quota_stats:
        if qs.used_ratio >= threshold:
            model = db.query(ModelConfig).filter(ModelConfig.id == qs.model_id).first()
            if model:
                alert_models.append(
                    {
                        "id": model.id,
                        "vendor": model.vendor,
                        "model_name": model.model_name,
                        "used_ratio": qs.used_ratio,
                    }
                )

    # 最近切换日志
    switch_logs = (
        db.query(OperationLog)
        .filter(OperationLog.log_type == 2)
        .order_by(desc(OperationLog.create_time))
        .limit(10)
        .all()
    )

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "stats": {
                "totalRequests": today_requests,
                "activeModels": active_models,
                "totalQuota": round(total_quota / 1000000, 2) if total_quota else 0,
                "switchCount": switch_count,
            },
            "currentModel": {
                "id": current_model.id,
                "vendor": current_model.vendor,
                "model_name": current_model.model_name,
                "priority": current_model.priority,
                "remain_quota": current_quota.remain_quota if current_quota else 0,
                "used_ratio": round(current_quota.used_ratio, 2)
                if current_quota
                else 0,
            }
            if current_model
            else None,
            "switchLogs": [
                {
                    "id": log.id,
                    "from_model": log.log_content.get("from_model")
                    if isinstance(log.log_content, dict)
                    else None,
                    "to_model": log.log_content.get("to_model")
                    if isinstance(log.log_content, dict)
                    else None,
                    "reason": log.log_content.get("reason")
                    if isinstance(log.log_content, dict)
                    else None,
                    "create_time": log.create_time.strftime("%Y-%m-%d %H:%M:%S")
                    if log.create_time
                    else None,
                }
                for log in switch_logs
            ],
            "alertModels": alert_models,
        },
    }


@stats_router.get("/api/stats/usage")
async def get_usage_trend(
    days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)
):
    """
    获取使用量趋势
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 按日期分组统计请求
    daily_stats = (
        db.query(
            func.date(OperationLog.create_time).label("date"),
            func.count(OperationLog.id).label("requests"),
        )
        .filter(OperationLog.log_type == 1, OperationLog.create_time >= start_date)
        .group_by(func.date(OperationLog.create_time))
        .order_by(func.date(OperationLog.create_time))
        .all()
    )

    # 转换为字典
    trend_dict = {str(stat.date): stat.requests for stat in daily_stats}

    # 生成完整日期序列
    full_trend = []
    for i in range(days):
        date = (end_date - timedelta(days=days - 1 - i)).date()
        date_str = date.strftime("%Y-%m-%d")
        full_trend.append({"date": date_str, "requests": trend_dict.get(str(date), 0)})

    return {"code": 200, "msg": "success", "data": {"trend": full_trend}}


@stats_router.get("/api/stats/models")
async def get_model_ranking(db: Session = Depends(get_db)):
    """
    获取模型使用排行
    """
    # 统计每个模型的请求次数
    model_stats = (
        db.query(
            OperationLog.model_id, func.count(OperationLog.id).label("request_count")
        )
        .filter(OperationLog.log_type == 1)
        .group_by(OperationLog.model_id)
        .order_by(desc(func.count(OperationLog.id)))
        .limit(10)
        .all()
    )

    total_requests = sum(stat.request_count for stat in model_stats) or 1

    rankings = []
    for stat in model_stats:
        model = db.query(ModelConfig).filter(ModelConfig.id == stat.model_id).first()

        if model:
            rankings.append(
                {
                    "model": f"{model.vendor} - {model.model_name}",
                    "requests": stat.request_count,
                    "percentage": round(stat.request_count / total_requests * 100, 2),
                }
            )

    return {"code": 200, "msg": "success", "data": {"rankings": rankings}}


@stats_router.get("/api/stats/quota")
async def get_quota_overview(db: Session = Depends(get_db)):
    """
    获取额度概览
    """
    quota_stats = db.query(QuotaStat).all()

    total = sum(q.total_quota for q in quota_stats)
    used = sum(q.used_quota for q in quota_stats)
    remain = total - used

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "total": total,
            "used": used,
            "remain": remain,
            "usageRate": round(used / total * 100, 2) if total > 0 else 0,
            "models": [
                {
                    "model_id": qs.model_id,
                    "total": qs.total_quota,
                    "used": qs.used_quota,
                    "remain": qs.remain_quota,
                    "usageRate": round(qs.used_ratio, 2),
                }
                for qs in quota_stats
            ],
        },
    }
