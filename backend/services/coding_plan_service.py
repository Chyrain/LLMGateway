"""
Coding Plan 套餐管理服务
支持多家厂商的 Coding Plan 套餐查询、同步和用量追踪
"""

import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from config.database import SessionLocal
from models.model_config import ModelConfig
from models.quota_stat import QuotaStat
from config.encryption import decrypt_api_key


class CodingPlanService:
    """Coding Plan 套餐管理服务"""

    # 加载配置
    _CONFIG_PATH = Path(__file__).parent.parent / "config" / "vendors.json"
    _CODING_PLANS = None

    @classmethod
    def _load_config(cls):
        """加载 Coding Plan 配置"""
        if cls._CODING_PLANS is None and cls._CONFIG_PATH.exists():
            with open(cls._CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._CODING_PLANS = data.get("coding_plans", {}).get("providers", {})
        return cls._CODING_PLANS or {}

    @classmethod
    def get_all_coding_plans(cls) -> Dict:
        """获取所有 Coding Plan 配置"""
        return cls._load_config()

    @classmethod
    def get_coding_plan(cls, provider: str) -> Optional[Dict]:
        """获取指定厂商的 Coding Plan 配置"""
        plans = cls._load_config()
        return plans.get(provider)

    @classmethod
    async def sync_quota(cls, model_id: int) -> Dict[str, Any]:
        """同步模型配额

        根据模型的厂商自动选择合适的同步方式
        """
        db = SessionLocal()
        try:
            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if not model:
                return {"success": False, "error": "模型不存在"}

            vendor = model.vendor
            model_name = model.model_name

            # 获取 API Key
            try:
                api_key = decrypt_api_key(model.api_key) if model.api_key else None
            except Exception:
                api_key = model.api_key

            if not api_key:
                return {"success": False, "error": "未配置 API Key"}

            # 根据厂商选择同步方式
            if vendor == "minimax":
                return await cls._sync_minimax_quota(model_id, api_key, model_name)
            elif vendor == "qwen" and api_key.startswith("sk-sp-"):
                return await cls._sync_aliyun_coding_plan(model_id, api_key, model_name)
            elif vendor == "zhipu":
                return await cls._sync_zhipu_quota(model_id, api_key, model_name)
            elif vendor == "deepseek":
                return await cls._sync_deepseek_balance(model_id, api_key)
            else:
                return {"success": False, "error": f"厂商 {vendor} 暂不支持自动同步"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @classmethod
    async def _sync_minimax_quota(
        cls, model_id: int, api_key: str, model_name: str
    ) -> Dict:
        """同步 MiniMax Coding Plan 配额"""
        try:
            url = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API 错误: {response.status_code}",
                    }

                data = response.json()
                model_remains = data.get("model_remains", [])

                if not model_remains:
                    return {"success": False, "error": "未获取到配额数据"}

                # 查找匹配的模型
                remain_info = None
                for remain in model_remains:
                    remain_model = remain.get("model_name", "")
                    if (
                        remain_model.lower() in model_name.lower()
                        or model_name.lower() in remain_model.lower()
                    ):
                        remain_info = remain
                        break

                if not remain_info:
                    remain_info = model_remains[0]

                # 解析配额
                total_count = remain_info.get("current_interval_total_count", 0)
                remaining_count = remain_info.get("current_interval_usage_count", 0)

                # MiniMax: 1 prompt ≈ 15 calls
                total_prompts = int(total_count / 15) if total_count > 0 else 0
                used_prompts = (
                    int((total_count - remaining_count) / 15) if total_count > 0 else 0
                )

                # 更新数据库
                cls._update_quota_db(
                    model_id,
                    {
                        "total_quota": total_prompts,
                        "used_quota": used_prompts,
                        "remain_quota": total_prompts - used_prompts,
                        "quota_unit": "prompts",
                        "plan_type": "coding",
                        "plan_name": "MiniMax Coding Plan",
                        "period_hours": 5,
                    },
                )

                return {
                    "success": True,
                    "data": {
                        "total": total_prompts,
                        "used": used_prompts,
                        "remain": total_prompts - used_prompts,
                        "unit": "prompts",
                    },
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def _sync_aliyun_coding_plan(
        cls, model_id: int, api_key: str, model_name: str
    ) -> Dict:
        """同步阿里云百炼 Coding Plan 配额

        注意: 阿里云百炼 Coding Plan 暂无公开的配额查询 API
        需要通过控制台手动查看或使用其他方式
        """
        # 阿里云百炼 Coding Plan 目前没有配额查询 API
        # 返回提示信息
        return {
            "success": False,
            "error": "阿里云百炼 Coding Plan 暂不支持 API 查询",
            "suggestion": "请访问 https://bailian.console.aliyun.com 查看配额",
        }

    @classmethod
    async def _sync_zhipu_quota(
        cls, model_id: int, api_key: str, model_name: str
    ) -> Dict:
        """同步智谱 GLM Coding Plan 配额"""
        # 智谱 Coding Plan 目前没有公开的配额查询 API
        return {
            "success": False,
            "error": "智谱 GLM Coding Plan 暂不支持 API 查询",
            "suggestion": "请访问 https://open.bigmodel.cn 查看配额",
        }

    @classmethod
    async def _sync_deepseek_balance(cls, model_id: int, api_key: str) -> Dict:
        """同步 DeepSeek 账户余额"""
        try:
            url = "https://api.deepseek.com/user/balance"
            headers = {"Authorization": f"Bearer {api_key}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API 错误: {response.status_code}",
                    }

                data = response.json()
                balance_infos = data.get("balance_infos", [])

                # 计算总余额
                total_balance = 0
                for info in balance_infos:
                    total_balance += float(info.get("total_balance", 0))

                # 更新数据库
                cls._update_quota_db(
                    model_id,
                    {
                        "total_quota": total_balance,
                        "used_quota": 0,
                        "remain_quota": total_balance,
                        "quota_unit": "USD",
                        "plan_type": "pay_as_you_go",
                        "plan_name": "DeepSeek 按量付费",
                    },
                )

                return {
                    "success": True,
                    "data": {
                        "balance": total_balance,
                        "currency": "USD",
                        "details": balance_infos,
                    },
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _update_quota_db(cls, model_id: int, quota_data: Dict):
        """更新数据库中的配额记录"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()

            if quota:
                quota.total_quota = quota_data.get("total_quota", 0)
                quota.used_quota = quota_data.get("used_quota", 0)
                quota.remain_quota = quota_data.get("remain_quota", 0)
                quota.quota_unit = quota_data.get("quota_unit", "tokens")
                quota.plan_type = quota_data.get("plan_type", "default")
                quota.plan_name = quota_data.get("plan_name", "")
                quota.period_hours = quota_data.get("period_hours", 0)
                quota.last_sync_time = datetime.now()
                quota.used_ratio = (
                    (quota.used_quota / quota.total_quota * 100)
                    if quota.total_quota > 0
                    else 0
                )
            else:
                quota = QuotaStat(
                    model_id=model_id,
                    total_quota=quota_data.get("total_quota", 0),
                    used_quota=quota_data.get("used_quota", 0),
                    remain_quota=quota_data.get("remain_quota", 0),
                    quota_unit=quota_data.get("quota_unit", "tokens"),
                    plan_type=quota_data.get("plan_type", "default"),
                    plan_name=quota_data.get("plan_name", ""),
                    period_hours=quota_data.get("period_hours", 0),
                    last_sync_time=datetime.now(),
                    sync_type=1,
                )
                db.add(quota)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @classmethod
    async def sync_all_models(cls) -> List[Dict]:
        """同步所有支持 Coding Plan 的模型配额"""
        db = SessionLocal()
        results = []

        try:
            # 获取所有启用的模型
            models = db.query(ModelConfig).filter(ModelConfig.status == 1).all()

            for model in models:
                # 检查是否支持同步
                vendor = model.vendor
                supports_sync = vendor in ["minimax", "deepseek"]

                # 通义千问 Coding Plan (sk-sp- 开头的 Key)
                if (
                    vendor == "qwen"
                    and model.api_key
                    and model.api_key.startswith("sk-sp-")
                ):
                    supports_sync = True

                if supports_sync:
                    result = await cls.sync_quota(model.id)
                    results.append(
                        {
                            "model_id": model.id,
                            "model_name": model.model_name,
                            "vendor": vendor,
                            **result,
                        }
                    )

        finally:
            db.close()

        return results

    @classmethod
    def get_package_info(cls, provider: str, package_name: str) -> Optional[Dict]:
        """获取指定套餐的详细信息"""
        plan = cls.get_coding_plan(provider)
        if not plan:
            return None

        packages = plan.get("packages", {})
        return packages.get(package_name)

    @classmethod
    def list_packages(cls, provider: str = None) -> Dict:
        """列出所有或指定厂商的套餐"""
        plans = cls._load_config()

        if provider:
            plan = plans.get(provider)
            if plan:
                return {provider: plan.get("packages", {})}
            return {}

        return {
            p: plan.get("packages", {})
            for p, plan in plans.items()
            if plan.get("packages")
        }
