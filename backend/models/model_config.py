from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from datetime import datetime
from config.database import Base


# 模型能力预设
_MODEL_CAPABILITIES = {
    # OpenAI
    "gpt-5": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "gpt-4o": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "gpt-4o-mini": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "gpt-4-turbo": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "gpt-4": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "gpt-3.5-turbo": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    # Anthropic
    "claude-4": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "claude-3-5-sonnet": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "claude-3-opus": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "claude-3-sonnet": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "claude-3-haiku": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    # Google
    "gemini-2": {"vision": True, "audio_input": True, "audio_output": True, "text": True},
    "gemini-1.5-pro": {"vision": True, "audio_input": True, "audio_output": False, "text": True},
    "gemini-1.5-flash": {"vision": True, "audio_input": True, "audio_output": False, "text": True},
    # 阿里通义
    "qwen-2.5": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "qwen-2": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "qwen-plus": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "qwen-turbo": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "qwen-vl": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    # 智谱
    "glm-4": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "glm-4v": {"vision": True, "audio_input": False, "audio_output": False, "text": True},
    "glm-3": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    # 讯飞星火
    "spark": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    "hunyuan": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
    # 豆包
    "doubao": {"vision": False, "audio_input": False, "audio_output": False, "text": True},
}


def _infer_capabilities(model_name: str, vendor: str = None) -> dict:
    """推断模型能力"""
    model_lower = model_name.lower()
    
    # 精确匹配
    if model_lower in _MODEL_CAPABILITIES:
        return _MODEL_CAPABILITIES[model_lower].copy()
    
    # 前缀匹配
    for key in _MODEL_CAPABILITIES:
        if model_lower.startswith(key):
            return _MODEL_CAPABILITIES[key].copy()
    
    # Vendor 特定推断
    if vendor:
        vendor_lower = vendor.lower()
        if "qwen" in vendor_lower or "tongyi" in vendor_lower:
            if "vl" in model_lower or "vision" in model_lower:
                return {"vision": True, "audio_input": False, "audio_output": False, "text": True}
        if "zhipu" in vendor_lower or "glm" in vendor_lower:
            if "v" in model_lower or "vision" in model_lower:
                return {"vision": True, "audio_input": False, "audio_output": False, "text": True}
    
    return {"vision": False, "audio_input": False, "audio_output": False, "text": True}


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
    plan_type = Column(
        String(20),
        default="default",
        comment="计划类型: default=默认, coding=Coding计划, reasoning=推理计划",
    )
    is_coding_model = Column(Integer, default=0, comment="是否为Coding模型: 0=否, 1=是")
    capabilities = Column(JSON, comment="模型能力: vision, audio_input, audio_output, text", default=None)
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def get_capabilities(self) -> dict:
        """获取模型能力"""
        if self.capabilities:
            return self.capabilities
        return _infer_capabilities(self.model_name, self.vendor)

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
            "plan_type": self.plan_type,
            "is_coding_model": self.is_coding_model,
            "capabilities": self.get_capabilities(),
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }
        if include_sensitive:
            from config.encryption import decrypt_api_key
            data["api_key"] = decrypt_api_key(self.api_key)
        return data
