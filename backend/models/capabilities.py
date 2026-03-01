"""
模型能力推断模块 - 用于检测模型是否支持多模态输入
"""

# 模型能力预设
_MODEL_CAPABILITIES = {
    # OpenAI
    "gpt-5": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "gpt-4o": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "gpt-4o-mini": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "gpt-4-turbo": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "gpt-4": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "gpt-3.5-turbo": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # Anthropic
    "claude-4": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "claude-3-5-sonnet": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "claude-3-opus": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "claude-3-sonnet": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "claude-3-haiku": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # Google
    "gemini-2": {
        "vision": True,
        "audio_input": True,
        "audio_output": True,
        "text": True,
    },
    "gemini-1.5-pro": {
        "vision": True,
        "audio_input": True,
        "audio_output": False,
        "text": True,
    },
    "gemini-1.5-flash": {
        "vision": True,
        "audio_input": True,
        "audio_output": False,
        "text": True,
    },
    # 阿里通义
    "qwen-2.5": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "qwen-2": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "qwen-plus": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "qwen-turbo": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "qwen-vl": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # 智谱
    "glm-4": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "glm-4v": {
        "vision": True,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    "glm-3": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # 讯飞星火
    "spark": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # 腾讯混元
    "hunyuan": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
    # 豆包
    "doubao": {
        "vision": False,
        "audio_input": False,
        "audio_output": False,
        "text": True,
    },
}


def get_model_capabilities(model_name: str, vendor: str = None) -> dict:
    """获取模型能力，根据模型名称自动推断

    Args:
        model_name: 模型名称
        vendor: 厂商名称 (可选)

    Returns:
        dict: 包含 vision, audio_input, audio_output, text 的能力字典
    """
    model_lower = model_name.lower()

    # 精确匹配
    if model_lower in _MODEL_CAPABILITIES:
        return _MODEL_CAPABILITIES[model_lower].copy()

    # 前缀匹配 (如 gpt-4o-2024-11-20 匹配 gpt-4o)
    for key in _MODEL_CAPABILITIES:
        if model_lower.startswith(key):
            return _MODEL_CAPABILITIES[key].copy()

    # 检查 vendor 特定模型
    if vendor:
        vendor_lower = vendor.lower()
        if "qwen" in vendor_lower or "tongyi" in vendor_lower:
            if "vl" in model_lower or "vision" in model_lower:
                return {
                    "vision": True,
                    "audio_input": False,
                    "audio_output": False,
                    "text": True,
                }
        if "zhipu" in vendor_lower or "glm" in vendor_lower:
            if "v" in model_lower or "vision" in model_lower:
                return {
                    "vision": True,
                    "audio_input": False,
                    "audio_output": False,
                    "text": True,
                }

    # 默认返回纯文本
    return {"vision": False, "audio_input": False, "audio_output": False, "text": True}


def get_vision_models() -> list:
    """获取所有支持视觉的模型列表"""
    return [
        name for name, caps in _MODEL_CAPABILITIES.items() if caps.get("vision", False)
    ]
