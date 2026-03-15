import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from config.database import SessionLocal
from models.quota_stat import QuotaStat
from models.model_config import ModelConfig
from config.encryption import decrypt_api_key


class QuotaMonitor:
    """额度监控服务"""

    # 各厂商的额度查询API配置
    QUOTA_APIS = {
        "openai": {
            "url": "https://api.openai.com/v1/dashboard/billing/usage",
            "response_field": "total_usage"
        },
        "zhipu": {
            "url": "https://open.bigmodel.cn/dev/manage/overview",
            "response_field": "quota"
        },
        "minimax": {
            "url": "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains",
            "response_field": "model_remains"
        }
    }

    # 配额阈值配置
    QUOTA_WARNING_RATIO = 90  # 即将耗尽阈值（90%）
    QUOTA_EXHAUSTED_RATIO = 100  # 已耗尽阈值（100%）

    @classmethod
    async def sync_quota_by_vendor(cls, vendor: str, model_id: int) -> bool:
        """根据厂商同步额度"""
        if vendor == "minimax":
            return await cls._sync_minimax_quota(model_id)

        if vendor not in cls.QUOTA_APIS:
            return False

        config = cls.QUOTA_APIS[vendor]
        # TODO: 实现其他厂商的额度查询
        return False

    @classmethod
    async def _sync_minimax_quota(cls, model_id: int) -> bool:
        """同步 MiniMax Coding Plan 额度"""
        db = SessionLocal()
        try:
            # 获取模型配置
            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if not model:
                print(f"[ERROR] 模型 {model_id} 不存在")
                return False

            # 先保存需要的信息
            model_name = model.model_name
            vendor = model.vendor

            # 获取 API Key
            try:
                api_key = decrypt_api_key(model.api_key) if model.api_key else None
            except Exception:
                api_key = model.api_key

            if not api_key:
                print(f"[ERROR] 模型 {model_id} 没有 API Key")
                return False

            # 调用 MiniMax 额度查询 API
            url = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"[ERROR] MiniMax API 返回错误: {response.status_code}")
                    return False

                data = response.json()
                model_remains = data.get("model_remains", [])

                if not model_remains:
                    print(f"[WARN] MiniMax API 未返回额度数据")
                    return False

                # 查找对应的模型
                model_name_map = {
                    "MiniMax-M2": "MiniMax-M2",
                    "MiniMax-M2.1": "MiniMax-M2.1",
                    "MiniMax-M2.5": "MiniMax-M2.5",
                    "MiniMax-M1": "MiniMax-M1"
                }

                target_model_name = None
                for key, value in model_name_map.items():
                    if value.lower() in model_name.lower() or model_name.lower() in value.lower():
                        target_model_name = key
                        break

                # 查找匹配的模型记录
                remain_info = None
                for remain in model_remains:
                    if target_model_name and remain.get("model_name") == target_model_name:
                        remain_info = remain
                        break
                    if not remain_info:
                        remain_info = remain

                if not remain_info:
                    print(f"[WARN] 未找到模型 {model_name} 的额度信息")
                    return False

                # 解析数据
                total_count = remain_info.get("current_interval_total_count", 0)
                remaining_count = remain_info.get("current_interval_usage_count", 0)
                start_time_ms = remain_info.get("start_time", 0)
                end_time_ms = remain_info.get("end_time", 0)

                # API 返回的是调用次数，需要转换为 prompt 次数
                # 根据用户反馈：总 40 prompts = 600 调用次数
                # 转换比例: 15 次调用 = 1 prompt
                # remaining_count 是剩余调用次数
                total_prompts = int(total_count / 15) if total_count > 0 else 0
                used_prompts = int((total_count - remaining_count) / 15) if total_count > 0 else 0

                # 记录已用 prompts 次数
                used_count = used_prompts

                # 转换时间戳
                period_start = datetime.fromtimestamp(start_time_ms / 1000) if start_time_ms else datetime.now()
                period_end = datetime.fromtimestamp(end_time_ms / 1000) if end_time_ms else None

                # 计算周期小时数
                period_hours = 0
                if period_start and period_end:
                    period_hours = int((period_end - period_start).total_seconds() / 3600)

                # 更新或创建配额记录
                quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()

                if quota:
                    quota.total_quota = total_prompts
                    quota.period_used = used_count
                    quota.period_start = period_start
                    quota.period_hours = period_hours
                    quota.quota_unit = "prompts"
                    quota.remain_quota = total_prompts - used_count
                    quota.used_ratio = (used_count / total_prompts * 100) if total_prompts > 0 else 0
                    quota.last_sync_time = datetime.now()
                else:
                    quota = QuotaStat(
                        model_id=model_id,
                        plan_type="coding",
                        plan_name=f"MiniMax {target_model_name or model_name} Coding Plan",
                        quota_unit="prompts",
                        period_hours=period_hours,
                        period_start=period_start,
                        period_used=used_count,
                        total_quota=total_prompts,
                        used_quota=0,
                        remain_quota=total_prompts - used_count,
                        used_ratio=(used_count / total_prompts * 100) if total_prompts > 0 else 0,
                        sync_type=1,
                        last_sync_time=datetime.now()
                    )
                    db.add(quota)

                db.commit()

                # 更新模型配额状态
                cls._update_model_quota_status(model_id, quota.used_ratio)

                print(f"[INFO] MiniMax 额度同步成功: {model_name}, 已用={used_count}, 总额={total_prompts}, 周期={period_hours}小时")
                return True

        except Exception as e:
            print(f"[ERROR] 同步 MiniMax 额度失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # ==================== 用量追踪 ====================

    @classmethod
    def calculate_usage(cls, vendor: str, response_data: Dict) -> Dict[str, int]:
        """根据响应计算Token使用量"""
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        if "usage" in response_data:
            usage_data = response_data["usage"]
            usage["prompt_tokens"] = usage_data.get("prompt_tokens", 0)
            usage["completion_tokens"] = usage_data.get("completion_tokens", 0)
            usage["total_tokens"] = usage_data.get("total_tokens", 0)

        return usage

    @classmethod
    def get_token_price(cls, vendor: str, model_name: str, is_input: bool = True) -> float:
        """获取Token单价（用于计算消耗）"""
        prices = {
            "openai": {
                "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
                "gpt-4o": {"input": 0.005, "output": 0.015}
            },
            "qwen": {
                "qwen-turbo": {"input": 0.0008, "output": 0.002},
                "qwen-plus": {"input": 0.002, "output": 0.006}
            }
        }

        vendor_prices = prices.get(vendor, {})
        model_prices = vendor_prices.get(model_name, {"input": 0, "output": 0})

        return model_prices["input"] if is_input else model_prices["output"]

    # ==================== 手动配额管理 ====================

    @classmethod
    def set_quota(
        cls,
        model_id: int,
        total_quota: float,
        plan_type: str = "default",
        plan_name: str = "",
        quota_unit: str = "tokens",
        period_hours: int = 0
    ) -> bool:
        """手动设置模型配额"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
            now = datetime.now()

            if quota:
                quota.total_quota = total_quota
                quota.plan_type = plan_type
                quota.plan_name = plan_name
                quota.quota_unit = quota_unit
                quota.period_hours = period_hours

                if period_hours > 0 and not quota.period_start:
                    quota.period_start = now
                    quota.period_used = 0

                if quota_unit == "tokens":
                    quota.remain_quota = total_quota - quota.used_quota
                    quota.used_ratio = (quota.used_quota / total_quota * 100) if total_quota > 0 else 0
                else:
                    quota.remain_quota = total_quota - quota.period_used
                    quota.used_ratio = (quota.period_used / total_quota * 100) if total_quota > 0 else 0

                cls._update_model_quota_status(model_id, quota.used_ratio)
            else:
                quota = QuotaStat(
                    model_id=model_id,
                    plan_type=plan_type,
                    plan_name=plan_name,
                    quota_unit=quota_unit,
                    period_hours=period_hours,
                    period_start=now if period_hours > 0 else None,
                    period_used=0,
                    total_quota=total_quota,
                    used_quota=0,
                    remain_quota=total_quota,
                    used_ratio=0,
                    sync_type=0,
                    last_sync_time=now
                )
                db.add(quota)

            db.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 设置配额失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @classmethod
    def get_quota(cls, model_id: int) -> Optional[Dict[str, Any]]:
        """获取模型配额信息"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
            if not quota:
                return None

            cls._check_period_reset(quota)

            return {
                "model_id": quota.model_id,
                "plan_type": quota.plan_type,
                "plan_name": quota.plan_name,
                "quota_unit": quota.quota_unit,
                "period_hours": quota.period_hours,
                "period_start": quota.period_start.isoformat() if quota.period_start else None,
                "period_used": quota.period_used,
                "total_quota": quota.total_quota,
                "used_quota": quota.used_quota,
                "remain_quota": quota.remain_quota,
                "used_ratio": quota.used_ratio,
                "sync_type": quota.sync_type,
                "last_sync_time": quota.last_sync_time.isoformat() if quota.last_sync_time else None,
                "update_time": quota.update_time.isoformat() if quota.update_time else None,
            }
        finally:
            db.close()

    @classmethod
    def get_all_quotas(cls) -> list:
        """获取所有模型配额信息"""
        db = SessionLocal()
        try:
            quotas = db.query(QuotaStat).all()
            result = []
            for quota in quotas:
                model = db.query(ModelConfig).filter(ModelConfig.id == quota.model_id).first()

                cls._check_period_reset(quota)
                db.commit()

                result.append({
                    "model_id": quota.model_id,
                    "model_name": model.model_name if model else "Unknown",
                    "vendor": model.vendor if model else "Unknown",
                    "plan_type": quota.plan_type,
                    "plan_name": quota.plan_name,
                    "quota_unit": quota.quota_unit,
                    "period_hours": quota.period_hours,
                    "period_start": quota.period_start.isoformat() if quota.period_start else None,
                    "period_used": quota.period_used,
                    "total_quota": quota.total_quota,
                    "used_quota": quota.used_quota,
                    "remain_quota": quota.remain_quota,
                    "used_ratio": quota.used_ratio,
                    "sync_type": quota.sync_type,
                    "last_sync_time": quota.last_sync_time.isoformat() if quota.last_sync_time else None,
                })
            return result
        finally:
            db.close()

    @classmethod
    def add_usage(cls, model_id: int, tokens_used: int = 1) -> bool:
        """累加使用量（支持 Token 和请求次数两种模式）"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()

            if not quota:
                print(f"[WARN] 模型 {model_id} 没有配额记录，无法累加用量")
                return False

            if quota.period_hours > 0 and not quota.period_start:
                quota.period_start = datetime.now()

            cls._check_period_reset(quota)

            if quota.quota_unit == "prompts":
                quota.period_used += tokens_used
                quota.remain_quota = quota.total_quota - quota.period_used
                quota.used_ratio = (quota.period_used / quota.total_quota * 100) if quota.total_quota > 0 else 0
                print(f"[INFO] 模型 {model_id} 请求次数已更新: period_used={quota.period_used}, remain={quota.remain_quota}")
            else:
                quota.used_quota += tokens_used
                quota.remain_quota = quota.total_quota - quota.used_quota
                quota.used_ratio = (quota.used_quota / quota.total_quota * 100) if quota.total_quota > 0 else 0
                print(f"[INFO] 模型 {model_id} Token用量已更新: used={quota.used_quota}, remain={quota.remain_quota}")

            cls._update_model_quota_status(model_id, quota.used_ratio)

            db.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 累加用量失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @classmethod
    def add_usage_from_response(cls, model_id: int, response_data: Dict, is_anthropic: bool = False) -> bool:
        """从 API 响应中提取并累加使用量

        Args:
            model_id: 模型 ID
            response_data: API 响应数据
            is_anthropic: 是否为 Anthropic 格式响应（已废弃，自动检测）
        """
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()

            if not quota:
                return False

            if quota.quota_unit == "prompts":
                return cls.add_usage(model_id, 1)
            else:
                # 自动检测响应格式并提取 usage
                # Anthropic 格式：usage 在响应顶层，使用 input_tokens/output_tokens
                # OpenAI 格式：usage 在响应顶层，使用 prompt_tokens/completion_tokens
                usage = response_data.get("usage", {})

                if not usage:
                    return False

                # 尝试 Anthropic 格式
                total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

                # 如果不是 Anthropic 格式，尝试 OpenAI 格式
                if total_tokens == 0:
                    total_tokens = usage.get("total_tokens", 0)

                if total_tokens > 0:
                    return cls.add_usage(model_id, total_tokens)

            return False
        finally:
            db.close()

    @classmethod
    def _update_model_quota_status(cls, model_id: int, used_ratio: float) -> None:
        """更新模型的配额状态"""
        db = SessionLocal()
        try:
            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if not model:
                return

            if used_ratio >= cls.QUOTA_EXHAUSTED_RATIO:
                model.quota_status = 0
            elif used_ratio >= cls.QUOTA_WARNING_RATIO:
                model.quota_status = 1
            else:
                model.quota_status = 2

            db.commit()
        except Exception as e:
            print(f"[ERROR] 更新模型配额状态失败: {e}")
            db.rollback()
        finally:
            db.close()

    # ==================== 达到限制处理 ====================

    @classmethod
    def _check_period_reset(cls, quota) -> bool:
        """检查并处理周期重置"""
        if not quota or quota.period_hours <= 0:
            return False

        now = datetime.now()
        if not quota.period_start:
            quota.period_start = quota.period_start or now
            quota.period_used = 0
            return True

        elapsed_hours = (now - quota.period_start).total_seconds() / 3600

        if elapsed_hours >= quota.period_hours:
            print(f"[INFO] 配额周期重置: model_id={quota.model_id}, 旧周期使用={quota.period_used}")
            quota.period_start = now
            quota.period_used = 0
            quota.remain_quota = quota.total_quota
            quota.used_ratio = 0
            return True

        return False

    @classmethod
    def is_quota_exhausted(cls, model_id: int) -> bool:
        """检查模型配额是否已耗尽"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
            if not quota or quota.total_quota <= 0:
                return False

            cls._check_period_reset(quota)
            db.commit()

            if quota.quota_unit == "prompts":
                return quota.period_used >= quota.total_quota
            else:
                return quota.used_ratio >= cls.QUOTA_EXHAUSTED_RATIO
        finally:
            db.close()

    @classmethod
    def filter_available_models(cls, models: list) -> list:
        """过滤掉已耗尽的模型"""
        available = []
        for model in models:
            if not cls.is_quota_exhausted(model.id):
                available.append(model)
            else:
                print(f"[INFO] 模型 ID {model.id} 配额已耗尽，已过滤")
        return available

    @classmethod
    def filter_available_models_by_ids(cls, model_ids: list, models: list) -> list:
        """根据 model_id 列表过滤掉已耗尽的模型"""
        available = []
        for i, model_id in enumerate(model_ids):
            if not cls.is_quota_exhausted(model_id):
                available.append(models[i])
            else:
                print(f"[INFO] 模型 ID {model_id} 配额已耗尽，已过滤")
        return available

    @classmethod
    def get_quota_status(cls, model_id: int) -> int:
        """获取模型配额状态"""
        db = SessionLocal()
        try:
            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if not model:
                return 2
            return model.quota_status
        finally:
            db.close()

    # ==================== 配额重置 ====================

    @classmethod
    def reset_quota(cls, model_id: int) -> bool:
        """重置模型配额"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
            if quota:
                quota.used_quota = 0
                quota.period_used = 0
                quota.remain_quota = quota.total_quota
                quota.used_ratio = 0
                db.commit()

            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if model:
                model.quota_status = 2
                db.commit()

            return True
        except Exception as e:
            print(f"[ERROR] 重置配额失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @classmethod
    def delete_quota(cls, model_id: int) -> bool:
        """删除模型配额记录"""
        db = SessionLocal()
        try:
            quota = db.query(QuotaStat).filter(QuotaStat.model_id == model_id).first()
            if quota:
                db.delete(quota)
                db.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 删除配额记录失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()
