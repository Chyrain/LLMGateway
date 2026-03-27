"""
四层日志追踪模块

追踪请求/响应在四个层次的数据流转：
- L1 原始输入 (Raw Input): Claude Code 发出的原始 HTTP 请求
- L2 网关输出 (Gateway Output): 网关转发给厂商 API 的请求
- L3 厂商响应 (Vendor Response): 厂商 API 返回的原始响应
- L4 最终输出 (Final Output): 网关返回给 Claude Code 的响应
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

# 日志配置
DEFAULT_LOG_FILE = "./data/debug_requests.log"
DEFAULT_MAX_LENGTH = 5000

# 全局配置（从环境变量读取）
_debug_config = {
    "enabled": os.getenv("DEBUG_LOG_ENABLED", "false").lower() == "true",
    "layers": os.getenv("DEBUG_LOG_LAYERS", "all"),  # all / input / output / none
    "max_length": int(os.getenv("DEBUG_LOG_MAX_LENGTH", str(DEFAULT_MAX_LENGTH))),
    "output": os.getenv("DEBUG_LOG_OUTPUT", "console"),  # console / file / both
    "log_file": os.getenv("DEBUG_LOG_FILE", DEFAULT_LOG_FILE),
}


def get_config(key: str, default=None):
    """获取配置值"""
    return _debug_config.get(key, default)


def set_config(key: str, value: Any):
    """设置配置值"""
    _debug_config[key] = value


def is_enabled() -> bool:
    """检查调试日志是否启用"""
    return _debug_config["enabled"]


def truncate_json(obj: Any, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """格式化 JSON 并截断"""
    json_str = json.dumps(obj, indent=2, ensure_ascii=False)
    if len(json_str) > max_length:
        return json_str[:max_length] + f"\n... [已截断，总长度：{len(json_str)}]"
    return json_str


def compare_fields(l1_data: Optional[Dict], l2_data: Optional[Dict],
                   l3_data: Optional[Dict], l4_data: Optional[Dict]) -> Dict[str, Any]:
    """比较关键字段的透传情况"""
    result = {
        "thinking_preserved": False,
        "reasoning_content_preserved": False,
        "tool_calls_preserved": False,
        "missing_fields": [],
    }

    # L1 -> L2: 检查 thinking 字段
    if l1_data and l2_data:
        l1_thinking = l1_data.get("thinking")
        l2_thinking = l2_data.get("thinking")
        result["thinking_preserved"] = (l1_thinking is not None and l2_thinking is not None)

        # 检查其他透传字段
        for field in ["reasoning_effort", "tools", "tool_choice", "response_format"]:
            if l1_data.get(field) is not None and l2_data.get(field) is None:
                result["missing_fields"].append(f"L1->L2: {field}")

    # L3 -> L4: 检查 reasoning_content 字段
    if l3_data and l4_data:
        # OpenAI 格式
        l3_reasoning = get_nested(l3_data, ["choices", 0, "message", "reasoning_content"])
        l4_reasoning = get_nested(l4_data, ["choices", 0, "message", "reasoning_content"])
        result["reasoning_content_preserved"] = (l3_reasoning is not None and l4_reasoning is not None)

        # 检查 tool_calls
        l3_tool_calls = get_nested(l3_data, ["choices", 0, "message", "tool_calls"])
        l4_tool_calls = get_nested(l4_data, ["choices", 0, "message", "tool_calls"])
        result["tool_calls_preserved"] = (l3_tool_calls is not None and l4_tool_calls is not None)

    return result


def get_nested(obj: Dict, keys: list):
    """安全获取嵌套字典的值"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        elif isinstance(obj, list) and isinstance(key, int):
            if key < len(obj):
                obj = obj[key]
            else:
                return None
        else:
            return None
    return obj


def format_layer_output(layer_name: str, data: Any, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """格式化层级输出"""
    if data is None:
        return f"【{layer_name}】\n(null)"

    if isinstance(data, dict):
        return f"【{layer_name}】\n{truncate_json(data, max_length)}"

    return f"【{layer_name}】\n{str(data)[:max_length]}"


def log_four_layers(
    l1_raw_input: Optional[Dict[str, Any]] = None,
    l2_gateway_output: Optional[Dict[str, Any]] = None,
    l3_vendor_response: Optional[Dict[str, Any]] = None,
    l4_final_output: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    model: Optional[str] = None,
    vendor: Optional[str] = None,
):
    """
    记录四层日志

    Args:
        l1_raw_input: L1 原始输入
        l2_gateway_output: L2 网关输出
        l3_vendor_response: L3 厂商响应
        l4_final_output: L4 最终输出
        request_id: 请求 ID
        model: 模型名称
        vendor: 厂商名称
    """
    if not is_enabled():
        return

    # 确定输出模式
    layers_mode = _debug_config["layers"]
    if layers_mode == "none":
        return
    if layers_mode == "input" and l3_vendor_response is not None:
        # 只记录输入相关
        pass
    if layers_mode == "output" and l1_raw_input is not None and l2_gateway_output is not None:
        # 只记录输出相关
        l1_raw_input = l2_gateway_output = None

    # 构建日志头部
    header = f"Request ID: {request_id or 'N/A'}"
    if model:
        header += f"  Model: {model}"
    if vendor:
        header += f"  Vendor: {vendor}"
    header += f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"

    # 构建日志内容
    separator = "═" * 60
    lines = [
        separator,
        f"[4-LAYER LOG] {header}",
        separator,
    ]

    # L1 原始输入
    if l1_raw_input is not None:
        lines.append("")
        lines.append("【L1 原始输入】← Client")
        lines.append(truncate_json(l1_raw_input, _debug_config["max_length"]))

    # L2 网关输出
    if l2_gateway_output is not None:
        lines.append("")
        lines.append("【L2 网关输出】→ Vendor API")
        lines.append(truncate_json(l2_gateway_output, _debug_config["max_length"]))

    # L3 厂商响应
    if l3_vendor_response is not None:
        lines.append("")
        lines.append("【L3 厂商响应】← Vendor API")
        lines.append(truncate_json(l3_vendor_response, _debug_config["max_length"]))

    # L4 最终输出
    if l4_final_output is not None:
        lines.append("")
        lines.append("【L4 最终输出】→ Client")
        lines.append(truncate_json(l4_final_output, _debug_config["max_length"]))

    # 字段对比
    if all([l1_raw_input, l2_gateway_output, l3_vendor_response, l4_final_output]):
        comparison = compare_fields(l1_raw_input, l2_gateway_output,
                                     l3_vendor_response, l4_final_output)
        lines.append("")
        lines.append(separator)
        lines.append("[字段对比]")

        thinking_status = "✓ 已透传" if comparison["thinking_preserved"] else "✗ 丢失"
        lines.append(f"  L1→L2: thinking 字段 {thinking_status}")

        reasoning_status = "✓ 已保留" if comparison["reasoning_content_preserved"] else "✗ 丢失"
        lines.append(f"  L3→L4: reasoning_content 字段 {reasoning_status}")

        tool_status = "✓ 已保留" if comparison["tool_calls_preserved"] else "✗ 丢失"
        lines.append(f"  L3→L4: tool_calls 字段 {tool_status}")

        if comparison["missing_fields"]:
            lines.append(f"  缺失字段：{', '.join(comparison['missing_fields'])}")

        lines.append(separator)

    log_content = "\n".join(lines)

    # 输出日志
    output_mode = _debug_config["output"]

    if output_mode in ("console", "both"):
        print(log_content)

    if output_mode in ("file", "both"):
        write_to_file(log_content)


def write_to_file(content: str):
    """写入日志文件"""
    log_file = _debug_config["log_file"]

    # 确保目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 写入文件
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n=== [{timestamp}] ===\n")
        f.write(content)
        f.write("\n")


def log_layer(layer: str, data: Any, context: Optional[Dict] = None):
    """
    记录单个层级的日志

    Args:
        layer: 层级标识 (L1/L2/L3/L4)
        data: 数据
        context: 上下文信息（如 request_id, model 等）
    """
    if not is_enabled():
        return

    layer_names = {
        "L1": "原始输入 ← Client",
        "L2": "网关输出 → Vendor",
        "L3": "厂商响应 ← Vendor",
        "L4": "最终输出 → Client",
    }

    separator = "─" * 60
    context_str = ""
    if context:
        parts = []
        if context.get("request_id"):
            parts.append(f"Request ID: {context['request_id']}")
        if context.get("model"):
            parts.append(f"Model: {context['model']}")
        if context.get("vendor"):
            parts.append(f"Vendor: {context['vendor']}")
        if parts:
            context_str = " | ".join(parts) + "\n"

    log_content = (
        f"\n{separator}\n"
        f"[{layer}] {layer_names.get(layer, layer)}\n"
        f"{context_str}"
        f"{truncate_json(data if isinstance(data, dict) else {'data': data}, _debug_config['max_length'])}\n"
        f"{separator}\n"
    )

    output_mode = _debug_config["output"]

    if output_mode in ("console", "both"):
        print(log_content)

    if output_mode in ("file", "both"):
        write_to_file(log_content)


def debug_logger(func):
    """
    装饰器：自动记录函数的输入输出作为调试日志

    用法:
        @debug_logger
        def my_function(arg1, arg2):
            ...
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not is_enabled():
            return await func(*args, **kwargs)

        # 记录输入
        log_layer("INPUT", {
            "function": func.__name__,
            "args": args[:3] if args else None,  # 只记录前 3 个参数避免过多
            "kwargs": {k: v for k, v in kwargs.items() if k != "api_key"}  # 隐藏 API Key
        })

        # 执行函数
        result = await func(*args, **kwargs)

        # 记录输出
        log_layer("OUTPUT", {
            "function": func.__name__,
            "result_keys": list(result.keys()) if isinstance(result, dict) else type(result).__name__
        })

        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not is_enabled():
            return func(*args, **kwargs)

        # 记录输入
        log_layer("INPUT", {
            "function": func.__name__,
            "args": args[:3] if args else None,
            "kwargs": {k: v for k, v in kwargs.items() if k != "api_key"}
        })

        # 执行函数
        result = func(*args, **kwargs)

        # 记录输出
        log_layer("OUTPUT", {
            "function": func.__name__,
            "result_keys": list(result.keys()) if isinstance(result, dict) else type(result).__name__
        })

        return result

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# 便捷函数
def log_request_start(request_data: Dict, request_id: str = None, model: str = None):
    """记录请求开始"""
    log_layer("L1", request_data, {"request_id": request_id, "model": model})


def log_gateway_forward(forward_data: Dict, request_id: str = None, model: str = None, vendor: str = None):
    """记录网关转发"""
    log_layer("L2", forward_data, {"request_id": request_id, "model": model, "vendor": vendor})


def log_vendor_response(response_data: Dict, request_id: str = None, vendor: str = None):
    """记录厂商响应"""
    log_layer("L3", response_data, {"request_id": request_id, "vendor": vendor})


def log_final_output(output_data: Dict, request_id: str = None, model: str = None):
    """记录最终输出"""
    log_layer("L4", output_data, {"request_id": request_id, "model": model})
