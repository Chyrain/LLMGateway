from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from datetime import datetime
from config.database import Base


class ModelConfig(Base):
    """模型配置表"""

    __tablename__ = "model_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor = Column(String(50), nullable=False, comment="厂商名称")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    api_base = Column(String(255), comment="API基础地址")
    api_path = Column(String(255), default="/v1/chat/completions", comment="请求路径")
    api_spec = Column(
        String(50),
        default="openai",
        comment="API规范: openai, anthropic, gemini, spark, custom",
    )
    api_key = Column(Text, comment="加密后的API Key")
    params = Column(JSON, comment="模型参数配置")
    param_mapping = Column(JSON, comment="参数映射规则")
    response_mapping = Column(JSON, comment="响应映射规则")
    priority = Column(Integer, default=100, comment="优先级(数字越小越高)")
    status = Column(Integer, default=0, comment="启用状态: 0=禁用, 1=启用")
    connect_status = Column(Integer, default=0, comment="连通状态: 0=断开, 1=连通")
    quota_status = Column(
        Integer, default=2, comment="额度状态: 0=已耗尽, 1=即将耗尽, 2=充足"
    )
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "vendor": self.vendor,
            "model_name": self.model_name,
            "api_base": self.api_base,
            "api_path": self.api_path,
            "api_spec": self.api_spec,
            "priority": self.priority,
            "status": self.status,
            "connect_status": self.connect_status,
            "quota_status": self.quota_status,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }
        if include_sensitive:
            from config.encryption import decrypt_api_key

            data["api_key"] = decrypt_api_key(self.api_key)
        return data
