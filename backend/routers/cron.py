"""
定时任务路由 - 包括配额同步、厂商信息更新等
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional, List
from datetime import datetime

from services.coding_plan_service import CodingPlanService
from services.quota_monitor import QuotaMonitor

cron_router = APIRouter()


@cron_router.get("/api/cron/status")
async def get_cron_status():
    """获取定时任务状态"""
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "last_sync_time": None,  # TODO: 从数据库获取
            "next_sync_time": None,
            "enabled": True,
        },
    }


@cron_router.post("/api/cron/sync-quota")
async def sync_quota_cron(
    background_tasks: BackgroundTasks, vendor: Optional[str] = None
):
    """手动触发配额同步

    Args:
        vendor: 可选，指定厂商同步。不传则同步所有支持的厂商
    """
    try:
        results = await CodingPlanService.sync_all_models()

        success_count = sum(1 for r in results if r.get("success"))
        fail_count = len(results) - success_count

        return {
            "code": 200,
            "msg": f"同步完成: {success_count} 成功, {fail_count} 失败",
            "data": {
                "total": len(results),
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
                "sync_time": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        return {"code": 500, "msg": f"同步失败: {str(e)}", "data": None}


@cron_router.post("/api/cron/sync-quota/{model_id}")
async def sync_single_model_quota(model_id: int):
    """同步单个模型的配额"""
    try:
        result = await CodingPlanService.sync_quota(model_id)

        if result.get("success"):
            return {"code": 200, "msg": "同步成功", "data": result}
        else:
            return {"code": 400, "msg": result.get("error", "同步失败"), "data": result}

    except Exception as e:
        return {"code": 500, "msg": f"同步失败: {str(e)}", "data": None}


@cron_router.get("/api/coding-plans")
async def list_coding_plans(vendor: Optional[str] = None):
    """获取 Coding Plan 套餐列表

    Args:
        vendor: 可选，筛选指定厂商
    """
    try:
        plans = CodingPlanService.get_all_coding_plans()

        if vendor:
            plan = plans.get(vendor)
            if plan:
                return {"code": 200, "msg": "success", "data": {vendor: plan}}
            return {"code": 404, "msg": f"厂商 {vendor} 无 Coding Plan", "data": {}}

        return {"code": 200, "msg": "success", "data": plans}
    except Exception as e:
        return {"code": 500, "msg": f"获取失败: {str(e)}", "data": {}}


@cron_router.get("/api/coding-plans/packages")
async def list_packages(vendor: Optional[str] = None):
    """获取套餐价格信息

    Args:
        vendor: 可选，筛选指定厂商
    """
    try:
        packages = CodingPlanService.list_packages(vendor)
        return {"code": 200, "msg": "success", "data": packages}
    except Exception as e:
        return {"code": 500, "msg": f"获取失败: {str(e)}", "data": {}}


@cron_router.post("/api/cron/update-vendor-info")
async def update_vendor_info(
    background_tasks: BackgroundTasks, vendor: Optional[str] = None
):
    """更新厂商模型信息（从网络获取最新数据）

    注意: 此功能需要网络请求各厂商官网获取最新模型信息
    """
    # TODO: 实现自动爬取厂商官网获取最新模型信息
    return {
        "code": 200,
        "msg": "功能开发中",
        "data": {"note": "此功能将自动从各厂商官网获取最新模型列表和价格信息"},
    }
