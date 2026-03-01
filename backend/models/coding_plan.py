"""
Coding Plan 数据库模型 - 存储用户的 Coding Plan 套餐配置
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from datetime import datetime
from config.database import Base


class CodingPlanConfig(Base):
    """Coding Plan 套餐配置表"""

    __tablename__ = "coding_plan_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 厂商信息
    vendor = Column(
        String(50),
        nullable=False,
        comment="厂商标识: aliyun_bailian, minimax, zhipu, volcengine",
    )
    vendor_name = Column(String(100), comment="厂商显示名称")

    # 套餐信息
    package_type = Column(String(50), comment="套餐类型: lite, pro, max 等")
    package_name = Column(String(100), comment="套餐显示名称")
    price_monthly = Column(Float, comment="月费(元)")
    price_first_month = Column(Float, comment="首月价(元)")

    # 配额限制
    quota_limits = Column(JSON, comment="配额限制: {per_5_hours, per_month}")
    quota_unit = Column(
        String(20), default="requests", comment="配额单位: requests, prompts"
    )

    # API 配置
    api_base = Column(String(255), comment="Coding Plan API Base URL")
    api_key = Column(Text, comment="加密后的 API Key")
    api_key_prefix = Column(String(20), comment="API Key 前缀特征")

    # 支持的模型
    supported_models = Column(JSON, comment="支持的模型列表")

    # 配额查询
    quota_query_method = Column(String(50), comment="配额查询方式: API, 控制台查看")
    quota_query_endpoint = Column(String(255), comment="配额查询 API 端点")
    quota_response_field = Column(String(100), comment="配额响应字段名")

    # 当前状态
    current_quota = Column(Integer, comment="当前剩余配额")
    total_quota = Column(Integer, comment="总配额")
    quota_updated_at = Column(DateTime, comment="配额最后更新时间")

    # 启用状态
    status = Column(Integer, default=1, comment="启用状态: 0=禁用, 1=启用")
    is_default = Column(Integer, default=0, comment="是否默认使用: 0=否, 1=是")

    # 时间戳
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
    expire_time = Column(DateTime, comment="套餐过期时间")

    # 备注
    notes = Column(Text, comment="备注信息")

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "vendor": self.vendor,
            "vendor_name": self.vendor_name,
            "package_type": self.package_type,
            "package_name": self.package_name,
            "price_monthly": self.price_monthly,
            "price_first_month": self.price_first_month,
            "quota_limits": self.quota_limits,
            "quota_unit": self.quota_unit,
            "api_base": self.api_base,
            "supported_models": self.supported_models or [],
            "quota_query_method": self.quota_query_method,
            "current_quota": self.current_quota,
            "total_quota": self.total_quota,
            "quota_updated_at": self.quota_updated_at.isoformat()
            if self.quota_updated_at
            else None,
            "status": self.status,
            "is_default": self.is_default,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
            "expire_time": self.expire_time.isoformat() if self.expire_time else None,
            "notes": self.notes,
        }

        if include_sensitive and self.api_key:
            from config.encryption import decrypt_api_key

            data["api_key"] = decrypt_api_key(self.api_key)

        return data


class CodingPlanUsage(Base):
    """Coding Plan 使用记录表"""

    __tablename__ = "coding_plan_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联配置
    plan_id = Column(Integer, nullable=False, comment="关联的 Coding Plan 配置 ID")
    model_config_id = Column(Integer, comment="关联的模型配置 ID")

    # 使用信息
    model_name = Column(String(100), comment="使用的模型名称")
    request_id = Column(String(100), comment="请求 ID")

    # Token 统计
    tokens_prompt = Column(Integer, default=0, comment="输入 Token 数")
    tokens_completion = Column(Integer, default=0, comment="输出 Token 数")
    tokens_total = Column(Integer, default=0, comment="总 Token 数")

    # 配额消耗（按套餐单位计算）
    quota_used = Column(Float, default=1, comment="消耗的配额单位")

    # 时间
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "model_config_id": self.model_config_id,
            "model_name": self.model_name,
            "request_id": self.request_id,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "quota_used": self.quota_used,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }
