"""
统一厂商模型配置 - 从 vendors.json 自动生成
此文件由代码生成，请勿手动修改
生成时间: 2026-03-01
"""

import json
from pathlib import Path

# 加载 JSON 配置
_CONFIG_PATH = Path(__file__).parent / "vendors.json"
_API_BASE_RULES_PATH = Path(__file__).parent / "vendors_api_base_rules.json"


def _load_vendor_config():
    """加载厂商配置"""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"vendors": {}}


def _load_api_base_rules():
    """加载 API Base Rules 配置"""
    if _API_BASE_RULES_PATH.exists():
        with open(_API_BASE_RULES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("vendors_api_base_rules", {})
    return {}


def get_api_spec_support(vendor_id: str) -> list:
    """获取厂商支持的 API 规范列表 (openai/anthropic)

    Args:
        vendor_id: 厂商 ID

    Returns:
        list: 支持的 API 规范列表，如 ["openai", "anthropic"]
    """
    api_base_rules_data = _API_BASE_RULES.get(vendor_id, {})
    return api_base_rules_data.get("api_spec_support", ["openai"])


def get_anthropic_compat_base(vendor_id: str) -> str:
    """获取厂商的 Anthropic 兼容 API Base 地址

    Args:
        vendor_id: 厂商 ID

    Returns:
        str: Anthropic 兼容的 API Base 地址，如果没有则返回空字符串
    """
    api_base_rules_data = _API_BASE_RULES.get(vendor_id, {})
    return api_base_rules_data.get("anthropic_compat_base", "")


def supports_anthropic_via_conversion(vendor_id: str) -> bool:
    """检查厂商是否支持通过转换模式处理 Anthropic 格式请求

    Args:
        vendor_id: 厂商 ID

    Returns:
        bool: 是否支持 Anthropic 转换模式
    """
    api_base_rules_data = _API_BASE_RULES.get(vendor_id, {})
    return api_base_rules_data.get("anthropic_via_conversion", False)


_VENDOR_DATA = _load_vendor_config()
_API_BASE_RULES = _load_api_base_rules()

# 厂商配置 (用于 gateway_core.py)
VENDOR_CONFIGS = {}

for vendor_id, vendor_info in _VENDOR_DATA.get("vendors", {}).items():
    VENDOR_CONFIGS[vendor_id] = {
        "name": vendor_info.get("name_zh", vendor_info.get("name")),
        "api_base": vendor_info.get("api_base", ""),
        "api_path": vendor_info.get("api_path", "/chat/completions"),
        "api_spec": vendor_info.get("api_spec", "openai"),
        "auth_header": vendor_info.get("auth_header", "Authorization"),
        "auth_format": vendor_info.get("auth_format", "Bearer"),
        "stream_support": vendor_info.get("stream_support", True),
    }

    # Coding Plan 配置
    coding_plan = vendor_info.get("coding_plan")
    if coding_plan:
        VENDOR_CONFIGS[vendor_id]["coding_plan"] = coding_plan

# 模型能力配置 (用于自动检测)
MODEL_CAPABILITIES = {}

for vendor_id, vendor_info in _VENDOR_DATA.get("vendors", {}).items():
    models = vendor_info.get("models", {})
    for model_id, model_info in models.items():
        MODEL_CAPABILITIES[model_id] = {
            "vendor": vendor_id,
            "context_length": model_info.get("context_length", 8192),
            "capabilities": model_info.get("capabilities", ["text"]),
            "vision": model_info.get("vision", False),
        }

# API 规范配置
API_SPECS = _VENDOR_DATA.get("api_specs", {})


def get_vendor_config(vendor_id: str) -> dict:
    """获取厂商配置"""
    return VENDOR_CONFIGS.get(vendor_id, VENDOR_CONFIGS.get("custom", {}))


def get_api_base_for_key(vendor_id: str, api_key: str, plan_type: str = None) -> str:
    """根据 API Key 前缀和套餐类型获取对应的 API Base 地址

    Args:
        vendor_id: 厂商 ID
        api_key: API Key
        plan_type: 套餐类型 (可选，如 "coding", "standard", "default")

    Returns:
        str: 对应的 API Base 地址
    """
    # 优先从独立配置文件加载 api_base_rules
    api_base_rules_data = _API_BASE_RULES.get(vendor_id, {})

    if api_base_rules_data:
        api_base_rules = api_base_rules_data.get("api_base_rules", [])
        if api_base_rules:
            for rule in api_base_rules:
                # 优先匹配 plan_type
                if plan_type:
                    match_pattern = rule.get("match_pattern")
                    rule_plan_type = rule.get("plan_type")
                    if (match_pattern and plan_type.lower() == match_pattern.lower()) or \
                       (rule_plan_type and plan_type.lower() == rule_plan_type.lower()):
                        return rule.get("api_base")

                # 然后匹配 API Key 前缀
                prefix = rule.get("api_key_prefix")
                if prefix is not None and api_key.startswith(prefix):
                    return rule.get("api_base")

            # 如果没有匹配到规则，返回第一个规则的 api_base
            return api_base_rules[0].get("api_base")

    # 从 vendors.json 中的配置加载（向后兼容）
    config = get_vendor_config(vendor_id)

    # 检查是否有 api_base_rules 配置
    api_base_rules = config.get("api_base_rules", [])
    if api_base_rules:
        for rule in api_base_rules:
            # 优先匹配 plan_type
            if plan_type:
                match_pattern = rule.get("match_pattern")
                if match_pattern and plan_type.lower() == match_pattern.lower():
                    return rule.get("api_base", config.get("api_base"))

            # 然后匹配 API Key 前缀
            prefix = rule.get("api_key_prefix")
            if prefix is not None and api_key.startswith(prefix):
                return rule.get("api_base", config.get("api_base"))

        # 如果没有匹配到规则，返回第一个规则的 api_base
        return api_base_rules[0].get("api_base", config.get("api_base"))

    # 检查 coding_plan 配置（向后兼容）
    coding_plan = config.get("coding_plan")
    if coding_plan:
        prefix = coding_plan.get("api_key_prefix", "")
        if prefix and api_key.startswith(prefix):
            return coding_plan.get("api_base", config.get("api_base"))

    # 返回默认 api_base
    return config.get("api_base", "")


def get_model_capabilities(model_name: str, vendor: str = None) -> dict:
    """获取模型能力

    Args:
        model_name: 模型名称
        vendor: 厂商ID (可选，用于辅助匹配)

    Returns:
        dict: 包含 vision, audio_input, audio_output, text, context_length 的能力字典
    """
    model_lower = model_name.lower()

    # 精确匹配
    if model_lower in MODEL_CAPABILITIES:
        caps = MODEL_CAPABILITIES[model_lower]
        capabilities = caps.get("capabilities", ["text"])
        return {
            "vision": "vision" in capabilities or caps.get("vision", False),
            "audio_input": "audio" in capabilities,
            "audio_output": False,
            "text": "text" in capabilities or True,
            "context_length": caps.get("context_length", 8192),
        }

    # 前缀匹配
    for key in MODEL_CAPABILITIES:
        if model_lower.startswith(key.lower()):
            caps = MODEL_CAPABILITIES[key]
            capabilities = caps.get("capabilities", ["text"])
            return {
                "vision": "vision" in capabilities or caps.get("vision", False),
                "audio_input": "audio" in capabilities,
                "audio_output": False,
                "text": "text" in capabilities or True,
                "context_length": caps.get("context_length", 8192),
            }

    # 根据名称特征推断
    vision_keywords = [
        "vision",
        "vl",
        "v-",
        "gemini",
        "gpt-4o",
        "gpt-4-turbo",
        "claude",
        "pixtral",
        "grok-2-vision",
    ]
    has_vision = any(kw in model_lower for kw in vision_keywords)

    return {
        "vision": has_vision,
        "audio_input": False,
        "audio_output": False,
        "text": True,
        "context_length": 8192,
    }


def get_all_vendors() -> list:
    """获取所有厂商列表"""
    return [
        {
            "id": vendor_id,
            "name": info.get("name_zh", info.get("name")),
            "api_base": info.get("api_base"),
            "api_spec": info.get("api_spec"),
            "stream_support": info.get("stream_support", True),
            "models": list(info.get("models", {}).keys()),
        }
        for vendor_id, info in _VENDOR_DATA.get("vendors", {}).items()
    ]


def get_vendor_models(vendor_id: str) -> list:
    """获取厂商支持的模型列表"""
    vendor_info = _VENDOR_DATA.get("vendors", {}).get(vendor_id, {})
    models = vendor_info.get("models", {})
    return [
        {
            "id": model_id,
            "context_length": model_info.get("context_length", 8192),
            "capabilities": model_info.get("capabilities", ["text"]),
            "vision": model_info.get("vision", False),
        }
        for model_id, model_info in models.items()
    ]
