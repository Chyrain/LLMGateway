"""
网关路由模块 - 只包含 LLM 请求转发相关接口

此模块包含：
- /v1/models - 模型列表（OpenAI 兼容）
- /v1/chat/completions - 聊天完成（OpenAI 兼容）
- /health - 健康检查
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Union
import json
import time
from datetime import datetime

from config.database import SessionLocal
from models.model_config import ModelConfig
from models.operation_log import OperationLog
from models.system_config import SystemConfig
from services.gateway_core import GatewayCore
from services.quota_monitor import QuotaMonitor
from services.sdk_gateway import SDKGateway
from services.debug_logger import log_four_layers, log_layer, is_enabled
from routers.config import config_store
from config.vendor_config import get_api_spec_support, get_anthropic_compat_base, supports_anthropic_via_conversion, get_api_base_for_key

# 创建路由
gateway_router = APIRouter(prefix="", tags=["网关接口"])


def verify_gateway_api_key(authorization: str) -> bool:
    """验证网关 API Key（从数据库读取配置）"""
    if not authorization or not authorization.startswith("Bearer "):
        return False

    api_key = authorization.replace("Bearer ", "")

    # 从数据库读取配置的 API Key
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "gateway_api_key").first()
        expected_key = config.config_value if config else None

        # 如果数据库没有配置，使用内存默认值作为后备
        if not expected_key:
            expected_key = config_store.get("gateway_api_key", "gtw_admin123")
    finally:
        db.close()

    return api_key == expected_key


# ==================== 请求模型 ====================
class ContentPart(BaseModel):
    """内容部分 - 支持文本或图片"""
    type: str = "text"  # "text" 或 "image_url"
    text: Optional[str] = None
    image_url: Optional[dict] = None


class ChatMessage(BaseModel):
    """聊天消息模型 - 支持 Vision 图片和 Tool 调用"""
    role: str
    content: Optional[str | List[ContentPart]] = None  # 支持纯文本、内容部分列表或 None（tool 角色）
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None  # assistant 角色的工具调用
    tool_call_id: Optional[str] = None  # tool 角色的工具调用 ID
    
    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> dict:
        """转换为字典，用于转发请求"""
        return self.model_dump(exclude_none=True)

class ChatCompletionRequest(BaseModel):
    """聊天完成请求模型 - 支持完整的 OpenAI API 字段"""
    # 核心必选字段
    model: Optional[str] = None  # 可选，不传时自动使用最高优先级模型
    messages: List[ChatMessage]
    
    # 常用可选字段
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = False
    stop: Optional[str | List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    
    # Function/Tool 相关
    response_format: Optional[Dict] = None
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[str | Dict] = None
    parallel_tool_calls: Optional[bool] = None
    function_call: Optional[str | Dict] = None
    
    # 高级字段
    seed: Optional[int] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    
    # Thinking/Reasoning 模式字段 (OpenAI o1/o3, DeepSeek R1, MiniMax 等)
    reasoning_effort: Optional[str] = None  # low/medium/high (OpenAI o1)
    thinking: Optional[Dict] = None  # Thinking 模式配置 (DeepSeek R1, MiniMax 等)

    model_config = ConfigDict(extra="allow")  # 允许透传任何其他字段

# ==================== Anthropic 兼容请求模型 ====================
class AnthropicMessage(BaseModel):
    """Anthropic 聊天消息模型"""
    role: str
    content: Union[str, List[dict]]  # 支持字符串或复杂对象数组（带 cache_control）


class AnthropicMessageRequest(BaseModel):
    """Anthropic 消息请求模型 - 支持完整的 Anthropic API 字段"""
    model: Optional[str] = None
    messages: List[AnthropicMessage]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: Optional[bool] = False
    system: Union[str, List[dict], None] = None  # 支持字符串或复杂对象数组

    # 工具调用相关字段
    tools: Optional[List[Dict]] = None  # Anthropic 格式工具定义
    tool_choice: Optional[str | Dict] = None  # 工具选择策略

    # 停止序列
    stop_sequences: Optional[List[str]] = None

    # 元数据（透传）
    metadata: Optional[Dict] = None

    model_config = ConfigDict(extra="allow")  # 允许透传任何其他字段


# ==================== 根路径和健康检查 ====================
@gateway_router.get("/")
async def root():
    """网关根路径"""
    return {"message": "灵模网关服务运行中", "version": "1.0.0", "mode": "gateway"}


@gateway_router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ==================== OpenAI 兼容接口 ====================
@gateway_router.get("/v1/models")
async def list_models_v1(authorization: Optional[str] = Header(None)):
    """OpenAI兼容的模型列表接口

    供第三方客户端检测可用的模型列表
    """
    if not verify_gateway_api_key(authorization):
        raise HTTPException(status_code=401, detail="API Key 无效")

    # 获取所有启用的模型
    db = SessionLocal()
    try:
        models = (
            db.query(ModelConfig)
            .filter(ModelConfig.status == 1)
            .order_by(ModelConfig.priority)
            .all()
        )

        # 如果没有启用任何模型，返回空列表
        if not models:
            return {"object": "list", "data": []}

        # 转换为 OpenAI 格式
        models_data = []

        # 只有启用了模型才添加 auto 选项
        models_data.append(
            {
                "id": "auto",
                "object": "model",
                "created": 0,
                "owned_by": "gateway",
                "description": "自动根据优先级切换模型",
                "capabilities": {"auto_switch": True, "priority_based": True},
            }
        )

        for model in models:
            # 获取模型能力
            capabilities = model.get_capabilities()
            
            models_data.append(
                {
                    "id": model.model_name,
                    "object": "model",
                    "created": int(model.create_time.timestamp())
                    if model.create_time
                    else 0,
                    "owned_by": model.vendor,
                    "capabilities": capabilities,
                }
            )

        return {"object": "list", "data": models_data}
    finally:
        db.close()


async def _stream_with_logging(
    model,
    request_data: dict,
    requested_model: Optional[str],
    client_ip: Optional[str],
    user_agent: Optional[str],
):
    """流式请求包装器，用于记录日志"""
    request_time = datetime.now()
    start_time = time.time()
    collected_content = []
    collected_tool_calls = []  # 初始化 tool_calls 收集器
    usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error_message = None
    full_response_json = {}  # 存储完整的响应JSON

    try:
        async for chunk in GatewayCore.stream_request(
            model.vendor, model.api_base, model.api_key, request_data, model.api_path
        ):
            yield chunk

            # 收集响应内容用于日志 - 支持 OpenAI 和 Ollama 格式
            if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                try:
                    data = json.loads(chunk[6:])
                    # 保存完整响应JSON（用于日志记录）
                    full_response_json = data

                    # OpenAI 格式: choices[0].delta.content
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected_content.append(content)

                        # 收集 tool_calls（流式返回）
                        if delta.get("tool_calls"):
                            collected_tool_calls.extend(delta["tool_calls"])
                        # 提取 usage
                        # 提取 finish_reason（通常在最后一个有内容的 chunk 中）
                        if choices[0].get("finish_reason"):
                            finish_reason = choices[0].get("finish_reason")
                        usage = data.get("usage")
                        if usage:
                            usage_data = usage
                    # Ollama 格式: message.content
                    elif "message" in data:
                        content = data.get("message", {}).get("content", "")
                        if content:
                            collected_content.append(content)

                        # 收集 tool_calls（流式返回）
                        if delta.get("tool_calls"):
                            collected_tool_calls.extend(delta["tool_calls"])
                except:
                    pass

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        # 记录日志
        try:
            response_time = datetime.now()
            duration_ms = (time.time() - start_time) * 1000

            db = SessionLocal()
            try:
                # 提取 messages
                messages = request_data.get("messages", [])
                response_content = "".join(collected_content)

                # 使用完整响应JSON（包含 id, model, choices, usage 等）
                response_json_str = json.dumps(full_response_json, ensure_ascii=False) if full_response_json else response_content

                print(f"[DEBUG] 开始记录访问日志, model_id={model.id}, request_data={request_data}")
                log = OperationLog(
                    log_type=1,  # 访问日志
                    model_id=model.id,
                    log_content=json.dumps(
                        {
                            "model": requested_model or "auto",
                            "actual_model": model.model_name,
                            "status": "success" if not error_message else "error",
                            "usage": usage_data,
                            "duration_ms": duration_ms,
                        }
                    ),
                    status=0 if error_message else 1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    request_content=json.dumps(request_data, ensure_ascii=False),
                    response_content=response_json_str[:10000],  # 限制长度，使用完整JSON
                    tokens_prompt=usage_data.get("prompt_tokens", 0),
                    tokens_completion=usage_data.get("completion_tokens", 0),
                    tokens_total=usage_data.get("total_tokens", 0),
                    error_message=error_message,
                )
                db.add(log)
                db.commit()
                print(
                    f"[SUCCESS] 流式响应记录完成: {model.vendor} - {model.model_name}, 耗时: {duration_ms:.2f}ms"
                )
            except Exception as log_e:
                print(f"[ERROR] 流式日志记录失败: {log_e}")
            finally:
                db.close()
        except Exception as e:
            print(f"[ERROR] 流式日志记录异常: {e}")


@gateway_router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
):
    """OpenAI兼容的Chat Completions接口，支持自动切换模型"""
    if not verify_gateway_api_key(authorization):
        raise HTTPException(status_code=401, detail="API Key 无效")

    # 获取客户端IP
    client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else ""

    requested_model = request.model
    print(
        f"[DEBUG] requested_model: '{requested_model}', type: {type(requested_model)}"
    )
    is_auto_mode = (
        requested_model in ["auto", "Auto", "AUTO", ""] or not requested_model
    )
    print(f"[DEBUG] is_auto_mode: {is_auto_mode}")

    # 定义当前路由端点类型
    route = "/v1/chat/completions"  # 当前函数处理的路由

    # 初始化日志变量
    log = None
    request_time = datetime.now()

    # 获取所有可用的模型（按优先级排序）
    db = SessionLocal()
    try:
        available_models = (
            db.query(ModelConfig)
            .filter(ModelConfig.status == 1, ModelConfig.connect_status == 1)
            .order_by(ModelConfig.priority)
            .all()
        )

        # 将模型对象从 session 中分离，避免后续访问时 detached 错误
        for model in available_models:
            db.refresh(model)  # 确保所有属性都已加载
        db.expunge_all()

        # 过滤掉已耗尽的模型
        available_models = QuotaMonitor.filter_available_models(available_models)

        if not available_models:
            # 记录无可用模型的错误日志
            response_time = datetime.now()
            duration_ms = int((response_time - request_time).total_seconds() * 1000)
            log = OperationLog(
                log_type=3,  # 错误日志
                model_id=0,
                log_content=json.dumps(
                    {
                        "model": requested_model or "auto",
                        "requested_model": requested_model,
                        "error": "无可用模型，请先配置模型",
                        "reason": "no_available_models",
                        "available_count": 0,
                        "client_ip": client_ip,
                        "user_agent": user_agent or "",
                    }
                ),
                status=0,
                request_time=request_time,
                response_time=response_time,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent or "",
                request_model=requested_model or "auto",
                error_message="无可用模型，请先配置模型",
                tokens_prompt=0,
                tokens_completion=0,
                tokens_total=0,
            )
            db.add(log)
            db.commit()
            raise HTTPException(status_code=503, detail="无可用模型，请先配置模型")

        # 决定要尝试的模型列表 - 按规则匹配，同规则内按优先级排序
        # 规则：
        # 1. Anthropic 请求 → 优先支持 Anthropic 的厂商 → 直接透传
        # 2. OpenAI 请求 → 优先支持 OpenAI 的厂商 → 直接透传
        # 3. 如果首选格式没有匹配厂商 → 转换为另一种格式 → 透传到支持该格式的厂商

        endpoint_type = "openai"  # 默认当前是 OpenAI 端点
        if route == "/v1/messages":
            endpoint_type = "anthropic"

        # 检查是否有指定模型
        if is_auto_mode:
            # auto 模式：先按规则匹配，再按优先级排序
            primary_models = []
            fallback_models = []

            for model in available_models:
                api_spec_support = get_api_spec_support(model.vendor)
                if endpoint_type in api_spec_support:
                    # 支持首选格式 → 直接透传
                    primary_models.append(model)
                else:
                    # 不支持首选格式，但可以转换
                    other_formats = {"openai", "anthropic"} - set(api_spec_support)
                    if other_formats:  # 支持另一种格式
                        fallback_models.append(model)

            # 按优先级排序
            primary_models = sorted(primary_models, key=lambda m: m.priority or 999)
            fallback_models = sorted(fallback_models, key=lambda m: m.priority or 999)

            # 优先使用支持首选格式的厂商（已按优先级排序）
            if primary_models:
                models_to_try = primary_models
                use_conversion = False  # 直接透传
                print(f"[INFO] auto 模式：找到 {len(primary_models)} 个支持 {endpoint_type} 格式的模型，按优先级直接透传")
            elif fallback_models:
                models_to_try = fallback_models
                use_conversion = True  # 需要转换格式
                print(f"[INFO] auto 模式：无支持 {endpoint_type} 格式的模型，将转换为另一种格式后透传")
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"无可用模型支持任何格式"
                )
        else:
            # 指定具体模型：按优先级顺序查找
            print(f"[DEBUG] Looking for model: '{requested_model}'")
            print(f"[DEBUG] Available models: {[m.model_name for m in available_models]}")

            # 按优先级顺序查找指定模型
            sorted_available = sorted(available_models, key=lambda m: m.priority or 999)
            target_model = None
            for model in sorted_available:
                if model.model_name == requested_model:
                    target_model = model
                    break

            if not target_model:
                raise HTTPException(
                    status_code=404,
                    detail=f"模型 '{requested_model}' 不存在或不可用"
                )

            # 检查厂商支持哪些格式
            api_spec_support = get_api_spec_support(target_model.vendor)
            vendor_supports_both = "openai" in api_spec_support and "anthropic" in api_spec_support

            # 如果厂商支持两种格式，根据请求端点自动适配
            if vendor_supports_both:
                models_to_try = [target_model]
                use_conversion = False
                print(f"[INFO] 指定模型 {requested_model} (厂商 {target_model.vendor} 支持双格式)，按请求端点 {endpoint_type} 透传")
            # 厂商只支持一种格式，检查是否需要转换
            elif endpoint_type in api_spec_support:
                models_to_try = [target_model]
                use_conversion = False
                print(f"[INFO] 指定模型 {requested_model} 支持 {endpoint_type} 格式，直接透传")
            elif "anthropic" in api_spec_support and endpoint_type == "openai":
                # OpenAI 请求，厂商只支持 Anthropic → 转换为 Anthropic
                models_to_try = [target_model]
                use_conversion = True
                print(f"[INFO] 指定模型 {requested_model} 只支持 anthropic，将 OpenAI 转换为 Anthropic 格式")
            elif "openai" in api_spec_support and endpoint_type == "anthropic":
                # Anthropic 请求，厂商只支持 OpenAI → 转换为 OpenAI
                models_to_try = [target_model]
                use_conversion = True
                print(f"[INFO] 指定模型 {requested_model} 只支持 openai，将 Anthropic 转换为 OpenAI 格式")
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"模型 '{requested_model}' 不支持请求的 {endpoint_type} 格式"
                )

            print(f"[DEBUG] target_model found: {target_model}, priority: {target_model.priority}, use_conversion: {use_conversion}")

        last_error = None
        successful_model = None
        response = None

        for model in models_to_try:
            request_time = datetime.now()
            start_time = time.time()

            try:
                print(f"[INFO] 使用模型: {model.vendor} - {model.model_name}")

                # 构建请求数据 - 透传所有用户字段，只替换 model
                request_data = {
                    "model": model.model_name,
                    "messages": [m.to_dict() for m in request.messages],
                }
                
                # 透传所有可选字段
                optional_fields = [
                    "temperature", "top_p", "n", "stream", "stop", "max_tokens",
                    "presence_penalty", "frequency_penalty", "logit_bias", "user",
                    "response_format", "tools", "tool_choice", "seed", "logprobs",
                    "top_logprobs", "parallel_tool_calls", "function_call",
                    "reasoning_effort", "thinking"  # Thinking 模式 (OpenAI o1/o3, DeepSeek R1, MiniMax)
                ]
                for field in optional_fields:
                    value = getattr(request, field, None)
                    if value is not None:
                        request_data[field] = value

                # 特殊处理：qwen thinking 模式不支持 tool_choice
                # 如果模型是 qwen 且开启了 thinking 模式，移除 tool_choice 参数
                if model.vendor == "qwen" and request_data.get("thinking"):
                    if "tool_choice" in request_data:
                        print(f"[WARN] qwen thinking 模式不支持 tool_choice，已移除")
                        del request_data["tool_choice"]

                # 特殊处理：百炼 API 不支持 thinking 参数
                # thinking 参数仅部分厂商支持（如 DeepSeek R1）
                if model.vendor in ["qwen", "bailian", "zhipu", "minimax"]:
                    if "thinking" in request_data:
                        print(f"[WARN] {model.vendor} API 不支持 thinking 参数，已移除")
                        del request_data["thinking"]
                
                # 透传任何其他额外字段
                for key, value in request.model_extra.items():
                    if key not in request_data and value is not None:
                        request_data[key] = value

                print(f"[DEBUG] 最终请求数据：{request_data}")

                # 生成请求 ID 用于四层日志追踪（传递给 GatewayCore 保持一致）
                import uuid
                request_id = str(uuid.uuid4())[:8]
                request_data["_request_id"] = request_id  # 透传到 GatewayCore

                # L1 日志：记录原始输入请求（在调用 GatewayCore 之前）
                if is_enabled():
                    log_layer("L1", {
                        "model": request.model or "auto",
                        "messages": [m.to_dict() for m in request.messages],
                        **{field: getattr(request, field, None) for field in optional_fields if getattr(request, field, None) is not None},
                        **{key: value for key, value in request.model_extra.items() if value is not None and key != "_request_id"},
                    }, context={"request_id": request_id, "model": request.model or "auto"})

                # 对于双格式厂商，根据请求端点选择对应 api_spec 的模型配置
                # 数据库中同一模型可能有两条记录 (openai 和 anthropic)，需要选择匹配当前请求端点的记录
                api_spec_support = get_api_spec_support(model.vendor)
                vendor_supports_both = "openai" in api_spec_support and "anthropic" in api_spec_support

                if vendor_supports_both and route == "/v1/messages":
                    # Anthropic 请求 → 查找 api_spec=anthropic 的模型记录
                    target_api_base = model.api_base
                    target_api_path = model.api_path
                    target_api_spec = model.api_spec
                    # 如果当前模型记录不匹配，查找正确的记录
                    if model.api_spec != "anthropic":
                        for m in available_models:
                            if m.model_name == model.model_name and m.api_spec == "anthropic":
                                target_api_base = m.api_base
                                target_api_path = m.api_path
                                target_api_spec = m.api_spec
                                print(f"[INFO] 厂商 {model.vendor} 支持双格式，Anthropic 请求使用：{target_api_base}{target_api_path}")
                                break
                elif vendor_supports_both and route == "/v1/chat/completions":
                    # OpenAI 请求 → 查找 api_spec=openai 的模型记录
                    target_api_base = model.api_base
                    target_api_path = model.api_path
                    target_api_spec = model.api_spec
                    # 如果当前模型记录不匹配，查找正确的记录
                    if model.api_spec != "openai":
                        for m in available_models:
                            if m.model_name == model.model_name and m.api_spec == "openai":
                                target_api_base = m.api_base
                                target_api_path = m.api_path
                                target_api_spec = m.api_spec
                                print(f"[INFO] 厂商 {model.vendor} 支持双格式，OpenAI 请求使用：{target_api_base}{target_api_path}")
                                break
                else:
                    # 单格式厂商，使用模型配置
                    target_api_base = model.api_base
                    target_api_path = model.api_path
                    target_api_spec = model.api_spec

                # 使用 SDK Gateway 进行原生格式透传（L2 → L3）
                response = await SDKGateway.sync_request(
                    api_spec=target_api_spec,
                    api_base=target_api_base,
                    api_key=model.api_key,
                    request_data=request_data,
                    api_path=target_api_path,
                )

                # 验证响应是否包含错误
                if "error" in response:
                    error_detail = response.get("error", "Unknown error")
                    error_type = response.get("error_type", "unknown_error")
                    raise ValueError(f"API 错误 ({error_type}): {error_detail}")

                # 验证响应是否有效（必须有 choices 且有内容或 tool_calls）
                choices = response.get("choices", [])
                if not choices:
                    raise ValueError("模型返回空响应")

                # 检查是否有有效内容（content 或 tool_calls 至少有一个非空）
                message = choices[0].get("message", {})
                has_content = bool(message.get("content"))
                has_tool_calls = bool(message.get("tool_calls"))

                if not has_content and not has_tool_calls:
                    raise ValueError("模型返回空响应")

                # 成功：记录详细日志并返回
                successful_model = model
                response_time = datetime.now()
                duration_ms = (time.time() - start_time) * 1000

                # 提取响应内容（支持 content 和 tool_calls）
                message = choices[0].get("message", {})
                response_content = message.get("content", "")
                tool_calls = message.get("tool_calls")
                finish_reason = choices[0].get("finish_reason", "stop")

                usage = response.get("usage", {})

                # 构建完整的响应 JSON 用于日志记录
                full_response = dict(response)  # 复制原始响应
                # 确保 choices 完整（保留 tool_calls）
                full_response["choices"] = [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content,
                        },
                        "finish_reason": finish_reason
                    }
                ]
                # 如果有 tool_calls，添加到响应中
                if tool_calls:
                    full_response["choices"][0]["message"]["tool_calls"] = tool_calls
                    full_response["choices"][0]["finish_reason"] = "tool_calls"
                response_json_str = json.dumps(full_response, ensure_ascii=False)
                
                print(f"[DEBUG] 开始记录访问日志, model_id={model.id}, response_content_len={len(response_json_str)}")
                log = OperationLog(
                    log_type=1,  # 访问日志
                    model_id=model.id,
                    log_content=json.dumps(
                        {
                            "model": requested_model or "auto",
                            "actual_model": model.model_name,
                            "status": "success",
                            "usage": usage,
                            "duration_ms": duration_ms,
                        }
                    ),
                    status=1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    request_content=json.dumps(request_data, ensure_ascii=False),
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    response_content=response_json_str[:50000],  # 增加到 50KB
                    tokens_prompt=usage.get("prompt_tokens", 0),
                    tokens_completion=usage.get("completion_tokens", 0),
                    tokens_total=usage.get("total_tokens", 0),
                    error_message=None,
                )
                db.add(log)
                db.commit()

                # 累加Token使用量
                QuotaMonitor.add_usage_from_response(model.id, response)

                print(
                    f"[SUCCESS] 模型响应成功: {model.vendor} - {model.model_name}, 耗时: {duration_ms:.2f}ms"
                )
                return response

            except Exception as e:
                last_error = e
                if isinstance(e, HTTPException):
                    error_msg = e.detail if e.detail else str(e)
                else:
                    error_msg = str(e) if str(e) else type(e).__name__
                response_time = datetime.now()
                duration_ms = (time.time() - start_time) * 1000

                print(
                    f"[ERROR] 模型 {model.vendor} - {model.model_name} 失败: {error_msg}"
                )

                # 记录详细失败日志
                log = OperationLog(
                    log_type=3,  # 错误日志
                    model_id=model.id,
                    log_content=json.dumps(
                        {
                            "model": requested_model or "auto",
                            "attempted_model": model.model_name,
                            "error": error_msg,
                            "duration_ms": duration_ms,
                        }
                    ),
                    status=0,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    request_content=json.dumps(request_data, ensure_ascii=False),
                    response_content="",
                    tokens_prompt=0,
                    tokens_completion=0,
                    tokens_total=0,
                    error_message=error_msg[:2000],  # 限制长度
                )
                db.add(log)
                db.commit()

                # 如果是指定模型模式，失败直接抛出错误
                if not is_auto_mode:
                    raise HTTPException(
                        status_code=500,
                        detail=f"模型 '{requested_model}' 请求失败: {error_msg}",
                    )

                # auto 模式继续尝试下一个
                continue

        # 所有模型都失败了
        error_detail = str(last_error) if last_error else "所有可用模型均失败"
        raise HTTPException(status_code=500, detail=error_detail)

    finally:
        db.close()


# ==================== Anthropic 兼容接口 ====================
@gateway_router.post("/v1/messages")
async def anthropic_messages(
    request: AnthropicMessageRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None, alias="authorization"),
    anthropic_version: Optional[str] = Header("2023-06-01", alias="anthropic-version"),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
):
    """Anthropic 兼容的 Messages 接口，支持自动切换模型

    支持的请求参数：
    - model: 模型名称（可选，不传时使用自动模式）
    - messages: 消息列表
    - max_tokens: 最大生成 token 数
    - temperature: 温度参数
    - top_p: top_p 参数
    - stream: 是否流式输出
    - system: 系统提示
    - stop_sequences: 停止序列
    """
    # 验证 API Key
    if not x_api_key and not authorization:
        raise HTTPException(status_code=401, detail="缺少 API Key")

    # 验证 API Key 有效性
    if authorization and not verify_gateway_api_key(authorization):
        raise HTTPException(status_code=401, detail="无效的 API Key")

    # 获取 API Key
    api_key = x_api_key

    # 获取客户端IP
    client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else ""

    requested_model = request.model
    is_auto_mode = requested_model in ["auto", "Auto", "AUTO", ""] or not requested_model

    # 定义当前路由端点类型
    route = "/v1/messages"  # 当前函数处理的路由

    request_time = datetime.now()
    db = SessionLocal()

    try:
        # 获取可用模型
        available_models = (
            db.query(ModelConfig)
            .filter(ModelConfig.status == 1, ModelConfig.connect_status == 1)
            .order_by(ModelConfig.priority)
            .all()
        )

        if not available_models:
            raise HTTPException(status_code=503, detail="无可用模型，请先配置模型")

        # 将模型对象从 session 中分离，避免后续访问时 detached 错误
        for model in available_models:
            db.refresh(model)  # 确保所有属性都已加载
        db.expunge_all()

        # 决定要尝试的模型列表
        if is_auto_mode:
            # auto 模式：根据请求端点类型过滤厂商
            # /v1/chat/completions 只选择支持 openai 的厂商
            # /v1/messages 选择支持 anthropic 的厂商（包括原生支持和转换模式支持）
            endpoint_type = "openai"  # 默认当前是 OpenAI 端点
            if route == "/v1/messages":
                endpoint_type = "anthropic"

            # 根据端点类型过滤模型
            models_to_try = []
            for model in available_models:
                api_spec_support = get_api_spec_support(model.vendor)
                # 检查是否支持 anthropic（包括原生或通过转换）
                if endpoint_type in api_spec_support or supports_anthropic_via_conversion(model.vendor):
                    models_to_try.append(model)

            # 如果没有找到匹配的模型，返回错误
            if not models_to_try:
                raise HTTPException(
                    status_code=503,
                    detail=f"无可用模型支持 {endpoint_type} 格式，请检查厂商配置"
                )
        else:
            # 指定具体模型：只试指定的模型
            endpoint_type = "openai"  # 默认当前是 OpenAI 端点
            if route == "/v1/messages":
                endpoint_type = "anthropic"

            # 优先选择 api_spec 匹配的模型
            target_model = next(
                (m for m in available_models if m.model_name == requested_model and m.api_spec == endpoint_type), None
            )
            # 如果没有找到匹配格式的模型，尝试查找支持转换模式的厂商
            if not target_model and endpoint_type == "anthropic":
                target_model = next(
                    (m for m in available_models if m.model_name == requested_model and supports_anthropic_via_conversion(m.vendor)), None
                )
            # 如果还是没有找到，尝试查找任意匹配的模型
            if not target_model:
                target_model = next(
                    (m for m in available_models if m.model_name == requested_model), None
                )
            if target_model:
                models_to_try = [target_model]
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"模型 '{requested_model}' 不存在或不可用",
                )

        last_error = None

        for model in models_to_try:
            request_time = datetime.now()
            start_time = time.time()

            try:
                # 检查厂商是否支持通过转换模式处理 Anthropic 请求
                use_conversion = supports_anthropic_via_conversion(model.vendor)

                if use_conversion:
                    # 转换模式：将 Anthropic 格式转换为 OpenAI 格式，使用 OpenAI SDK 转发
                    # 根据 API Key 动态获取正确的 API Base 地址
                    target_api_base = get_api_base_for_key(model.vendor, model.api_key, None)

                    # 将 Anthropic 格式请求转换为 OpenAI 格式
                    # Anthropic messages -> OpenAI messages
                    openai_messages = []
                    system_prompt = None

                    # 处理 system 参数
                    if request.system:
                        if isinstance(request.system, str):
                            system_prompt = request.system
                        elif isinstance(request.system, list):
                            # Anthropic system 可以是字符串数组或 content blocks 数组
                            system_parts = []
                            for item in request.system:
                                if isinstance(item, str):
                                    system_parts.append(item)
                                elif isinstance(item, dict) and item.get("type") == "text":
                                    system_parts.append(item.get("text", ""))
                            system_prompt = "\n".join(system_parts)

                    # 处理 messages
                    for msg in request.messages:
                        openai_msg = {"role": msg.role, "content": msg.content}
                        openai_messages.append(openai_msg)

                    # 构建 OpenAI 格式请求
                    request_data = {
                        "model": model.model_name,
                        "messages": openai_messages,
                        "max_tokens": request.max_tokens or 1024,
                        "stream": request.stream,
                    }

                    # 添加 system prompt（如果存在）
                    if system_prompt:
                        # 在 messages 前添加 system 消息
                        request_data["messages"] = [{"role": "system", "content": system_prompt}] + openai_messages

                    # 透传工具相关参数（百炼原生支持 Anthropic 格式，直接透传）
                    if request.tools:
                        request_data["tools"] = request.tools
                    if request.tool_choice:
                        request_data["tool_choice"] = request.tool_choice

                    # 透传其他参数
                    if request.temperature is not None:
                        request_data["temperature"] = request.temperature
                    if request.top_p is not None:
                        request_data["top_p"] = request.top_p
                    if request.stop_sequences:
                        request_data["stop"] = request.stop_sequences

                    # 透传 model_extra 中的额外参数
                    for key, value in request.model_extra.items():
                        if key not in request_data and value is not None:
                            request_data[key] = value

                    # 特殊处理：百炼 API 不支持 thinking 参数
                    # thinking 参数仅部分厂商支持（如 DeepSeek R1）
                    if model.vendor in ["qwen", "bailian", "zhipu", "minimax"]:
                        if "thinking" in request_data:
                            print(f"[WARN] {model.vendor} API 不支持 thinking 参数，已移除")
                            del request_data["thinking"]

                    # 生成请求 ID 用于日志追踪
                    import uuid
                    request_id = str(uuid.uuid4())[:8]
                    request_data["_request_id"] = request_id

                    # L1 日志：记录原始输入请求
                    if is_enabled():
                        log_layer("L1", {
                            "endpoint": "anthropic",
                            "model": request.model or "auto",
                            "messages": [msg.model_dump() for msg in request.messages],
                            "system": request.system,
                        }, context={"request_id": request_id, "model": request.model or "auto"})

                    # 流式响应
                    if request.stream:
                        return StreamingResponse(
                            _conversion_anthropic_to_openai_stream_with_logging(
                                model,
                                request_data,
                                requested_model,
                                client_ip,
                                user_agent,
                                request.max_tokens or 1024,
                                target_api_base,
                                request.tools,
                            ),
                            media_type="text/event-stream",
                            headers={
                                "Cache-Control": "no-cache",
                                "Connection": "keep-alive",
                                "anthropic-version": anthropic_version,
                            },
                        )
                    else:
                        # 非流式响应 - 使用 OpenAI SDK 转发
                        response = await SDKGateway.sync_request(
                            api_spec="openai",
                            api_base=target_api_base,
                            api_key=model.api_key,
                            request_data=request_data,
                            api_path=model.api_path,
                        )

                        # 将 OpenAI 响应转换为 Anthropic 格式
                        if "error" in response:
                            error_detail = response.get("error", "Unknown error")
                            error_type = response.get("error_type", "unknown_error")
                            raise ValueError(f"API 错误 ({error_type}): {error_detail}")

                        # 转换 OpenAI 响应为 Anthropic 格式
                        response = _convert_openai_to_anthropic_response(response)
                else:
                    # 原生模式：使用 Anthropic SDK 直接转发
                    # 对于双格式厂商，根据请求端点选择对应 api_spec 的模型配置
                    api_spec_support = get_api_spec_support(model.vendor)
                    vendor_supports_both = "openai" in api_spec_support and "anthropic" in api_spec_support

                    if vendor_supports_both:
                        # 双格式厂商，查找 api_spec=anthropic 的模型记录
                        target_api_base = model.api_base
                        target_api_path = model.api_path
                        # 如果当前模型记录不是 anthropic，查找正确的记录
                        if model.api_spec != "anthropic":
                            for m in available_models:
                                if m.model_name == model.model_name and m.api_spec == "anthropic":
                                    target_api_base = m.api_base
                                    target_api_path = m.api_path
                                    print(f"[INFO] 厂商 {model.vendor} 支持双格式，Anthropic 请求使用：{target_api_base}{target_api_path}")
                                    break
                    else:
                        # 单格式厂商，使用模型配置
                        anthropic_compat_base = get_anthropic_compat_base(model.vendor)
                        target_api_base = anthropic_compat_base if anthropic_compat_base else model.api_base
                        target_api_path = model.api_path

                    request_data = {
                        "model": model.model_name,
                        "messages": [msg.model_dump() for msg in request.messages],
                        "max_tokens": request.max_tokens or 1024,
                        "stream": request.stream,
                    }
                    # 透传 system（支持复杂对象数组）
                    if request.system is not None:
                        request_data["system"] = request.system
                    # 透传工具相关参数
                    if request.tools:
                        request_data["tools"] = request.tools
                    if request.tool_choice:
                        request_data["tool_choice"] = request.tool_choice
                    # 透传其他参数
                    if request.temperature is not None:
                        request_data["temperature"] = request.temperature
                    if request.top_p is not None:
                        request_data["top_p"] = request.top_p
                    if request.stop_sequences:
                        request_data["stop_sequences"] = request.stop_sequences
                    if request.metadata:
                        request_data["metadata"] = request.metadata
                    # 透传 model_extra 中的所有额外参数
                    for key, value in request.model_extra.items():
                        if key not in request_data and value is not None:
                            request_data[key] = value

                    # 流式响应 - 使用 Anthropic SDK 流式转发
                    if request.stream:
                        return StreamingResponse(
                            _sdk_anthropic_stream_with_logging(
                                model,
                                request_data,
                                requested_model,
                                client_ip,
                                user_agent,
                                request.max_tokens or 1024,
                                target_api_base,
                            ),
                            media_type="text/event-stream",
                            headers={
                                "Cache-Control": "no-cache",
                                "Connection": "keep-alive",
                                "anthropic-version": anthropic_version,
                            },
                        )
                    else:
                        # 非流式响应 - 使用 Anthropic SDK 转发
                        response = await SDKGateway.sync_request(
                            api_spec="anthropic",
                            api_base=target_api_base,
                            api_key=model.api_key,
                            request_data=request_data,
                            api_path=target_api_path,
                        )

                # 验证响应是否包含错误
                if "error" in response:
                    error_detail = response.get("error", "Unknown error")
                    error_type = response.get("error_type", "unknown_error")
                    raise ValueError(f"API 错误 ({error_type}): {error_detail}")

                # 验证响应（支持 text 和 tool_use 内容块）
                content_blocks = response.get("content", [])
                has_content = False
                has_tool_use = False

                for block in content_blocks:
                    if isinstance(block, dict):
                        block_type = block.get("type", "")
                        if block_type == "text" and block.get("text", "").strip():
                            has_content = True
                        elif block_type == "tool_use":
                            has_tool_use = True

                if not has_content and not has_tool_use:
                    raise ValueError("模型返回空响应")

                # 成功：记录日志并返回响应
                response_time = datetime.now()
                duration_ms = (time.time() - start_time) * 1000

                # Anthropic SDK 返回的已经是 Anthropic 格式，直接透传
                response_content = ""
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_content = block.get("text", "")
                        break

                usage = response.get("usage", {})
                usage_input = usage.get("input_tokens", 0)
                usage_output = usage.get("output_tokens", 0)

                # 记录日志
                log = OperationLog(
                    log_type=1,
                    model_id=model.id,
                    log_content=json.dumps({
                        "model": requested_model or "auto",
                        "actual_model": model.model_name,
                        "status": "success",
                        "api": "anthropic_sdk",
                        "duration_ms": duration_ms,
                    }),
                    status=1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    request_content=json.dumps(request_data, ensure_ascii=False),
                    response_content=json.dumps(response, ensure_ascii=False)[:10000],
                    tokens_prompt=usage_input,
                    tokens_completion=usage_output,
                    tokens_total=usage_input + usage_output,
                )
                db.add(log)
                db.commit()

                # 累加 Token 使用量 - 支持 Anthropic 格式
                try:
                    QuotaMonitor.add_usage(model.id, usage_input + usage_output)
                except:
                    pass

                # 直接返回 Anthropic 格式响应 - 完整透传 content（包括 text 和 tool_use）
                content_blocks = response.get("content", [])

                return {
                    "id": response.get("id", f"msg_{int(time.time() * 1000)}"),
                    "type": "message",
                    "role": "assistant",
                    "content": content_blocks,  # 完整透传 content 数组
                    "model": model.model_name,
                    "stop_reason": response.get("stop_reason", "end_turn"),
                    "stop_sequence": response.get("stop_sequence"),
                    "usage": {
                        "input_tokens": usage_input,
                        "output_tokens": usage_output,
                    },
                }

            except Exception as e:
                last_error = e
                if isinstance(e, HTTPException):
                    error_msg = e.detail if e.detail else str(e)
                else:
                    error_msg = str(e) if str(e) else type(e).__name__

                response_time = datetime.now()
                duration_ms = (time.time() - start_time) * 1000

                # 记录失败日志
                log = OperationLog(
                    log_type=3,
                    model_id=model.id,
                    log_content=json.dumps({
                        "model": requested_model or "auto",
                        "attempted_model": model.model_name,
                        "api": "anthropic",
                        "error": error_msg,
                        "duration_ms": duration_ms,
                    }),
                    status=0,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    error_message=error_msg[:2000],
                )
                db.add(log)
                db.commit()

                if not is_auto_mode:
                    raise HTTPException(
                        status_code=500,
                        detail=f"模型请求失败: {error_msg}",
                    )
                continue

        error_detail = str(last_error) if last_error else "所有可用模型均失败"
        raise HTTPException(status_code=500, detail=error_detail)

    finally:
        db.close()


async def _anthropic_stream_with_logging(
    model,
    request_data: dict,
    requested_model: Optional[str],
    client_ip: Optional[str],
    user_agent: Optional[str],
    max_tokens: int,
):
    """Anthropic 流式请求包装器，用于记录日志"""
    request_time = datetime.now()
    start_time = time.time()
    collected_content = []
    usage_data = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    error_message = None
    full_response_json = {}  # 存储完整的响应JSON
    finish_reason = None  # 记录停止原因

    try:
        async for chunk in GatewayCore.stream_request(
            model.vendor, model.api_base, model.api_key, request_data, model.api_path
        ):
            yield chunk

            # 收集响应内容
            if chunk.startswith("data: ") and chunk != "data: [DONE]\n\n":
                try:
                    data = json.loads(chunk[6:])
                    # 保存完整响应JSON
                    full_response_json = data
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected_content.append(content)

                        # 收集 tool_calls（流式返回）
                        if delta.get("tool_calls"):
                            collected_tool_calls.extend(delta["tool_calls"])
                        # 提取 finish_reason（通常在最后一个有内容的 chunk 中）
                        if choices[0].get("finish_reason"):
                            finish_reason = choices[0].get("finish_reason")
                    # 收集 usage 信息（通常在最后一个 chunk 中）
                    usage = data.get("usage")
                    if usage:
                        usage_data["prompt_tokens"] = usage.get("prompt_tokens", 0)
                        usage_data["completion_tokens"] = usage.get("completion_tokens", 0)
                        usage_data["total_tokens"] = usage.get("total_tokens", 0)

                except:
                    pass

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        try:
            response_time = datetime.now()
            duration_ms = (time.time() - start_time) * 1000
            response_content = "".join(collected_content)
            # 使用完整响应JSON
            response_json_str = json.dumps(full_response_json, ensure_ascii=False) if full_response_json else response_content

            db = SessionLocal()
            try:
                log = OperationLog(
                    log_type=1,
                    model_id=model.id,
                    log_content=json.dumps({
                        "model": requested_model or "auto",
                        "actual_model": model.model_name,
                        "api": "anthropic",
                        "status": "success" if not error_message else "error",
                        "duration_ms": duration_ms,
                    }),
                    status=0 if error_message else 1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    response_content=response_json_str[:10000],  # 使用完整JSON
                    tokens_prompt=usage_data.get("prompt_tokens", 0),
                    tokens_completion=usage_data.get("completion_tokens", 0),
                    tokens_total=usage_data.get("prompt_tokens", 0) + usage_data.get("completion_tokens", 0),
                    error_message=error_message,
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[ERROR] Anthropic 流式日志记录异常: {e}")




async def _sdk_anthropic_stream_with_logging(
    model,
    request_data: dict,
    requested_model: Optional[str],
    client_ip: Optional[str],
    user_agent: Optional[str],
    max_tokens: int,
    api_base_override: Optional[str] = None,
):
    """Anthropic SDK 流式请求包装器，用于记录日志

    Args:
        model: 模型配置对象
        request_data: 请求数据
        requested_model: 请求的模型名称
        client_ip: 客户端 IP
        user_agent: User-Agent
        max_tokens: 最大 Token 数
        api_base_override: 可选的 API Base 地址覆盖

    Anthropic SDK 流式事件格式：
    - event: message_start / data: {"type": "message_start", "message": {...}}
    - event: content_block_start / data: {"type": "content_block_start", "index": 0, "content_block": {...}}
    - event: content_block_delta / data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "..."}}
    - event: content_block_stop / data: {"type": "content_block_stop", "index": 0}
    - event: message_delta / data: {"type": "message_delta", "delta": {"stop_reason": "...", ...}, "usage": {...}}
    - event: message_stop / data: {"type": "message_stop"}
    """
    request_time = datetime.now()
    start_time = time.time()
    collected_content = []
    collected_tool_calls = []  # 初始化 tool_calls 收集器
    usage_data = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    error_message = None
    full_response_json = {}  # 存储完整的响应 JSON
    finish_reason = None  # 记录停止原因

    try:
        # 使用 SDKGateway 进行 Anthropic 格式流式转发
        async for chunk in SDKGateway.stream_request(
            api_spec="anthropic",
            api_base=api_base_override if api_base_override else model.api_base,
            api_key=model.api_key,
            request_data=request_data,
        ):
            yield chunk

            # 收集响应内容（Anthropic 格式）
            if chunk.startswith("data: "):
                try:
                    data_str = chunk[6:].strip()
                    if data_str and data_str != "[DONE]":
                        data = json.loads(data_str)
                        full_response_json = data

                        # content_block_delta: 收集文本内容
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                content = delta.get("text", "")
                                if content:
                                    collected_content.append(content)

                        # 收集 tool_calls（流式返回）
                        if delta.get("tool_calls"):
                            collected_tool_calls.extend(delta["tool_calls"])

                        # message_delta: 收集 stop_reason 和 usage
                        if data.get("type") == "message_delta":
                            delta = data.get("delta", {})
                            if delta and "stop_reason" in delta:
                                finish_reason = delta["stop_reason"]

                            usage = data.get("usage")
                            if usage:
                                usage_data["input_tokens"] = usage.get("input_tokens", 0)
                                usage_data["output_tokens"] = usage.get("output_tokens", 0)
                                usage_data["total_tokens"] = usage_data["input_tokens"] + usage_data["output_tokens"]

                        # message_start: 收集初始 usage（如果有）
                        if data.get("type") == "message_start":
                            message = data.get("message", {})
                            if message and "usage" in message:
                                usage = message["usage"]
                                usage_data["input_tokens"] = usage.get("input_tokens", 0)

                except Exception as e:
                    print(f"[WARN] 解析 Anthropic 流式数据失败：{e}")
                    pass

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        try:
            response_time = datetime.now()
            duration_ms = (time.time() - start_time) * 1000
            response_content = "".join(collected_content)
            response_json_str = json.dumps(full_response_json, ensure_ascii=False) if full_response_json else response_content

            db = SessionLocal()
            try:
                log = OperationLog(
                    log_type=1,
                    model_id=model.id,
                    log_content=json.dumps({
                        "model": requested_model or "auto",
                        "actual_model": model.model_name,
                        "api": "anthropic_sdk",
                        "status": "success" if not error_message else "error",
                        "duration_ms": duration_ms,
                        "finish_reason": finish_reason,
                    }),
                    status=0 if error_message else 1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    response_content=response_json_str[:10000],
                    tokens_prompt=usage_data.get("input_tokens", 0),
                    tokens_completion=usage_data.get("output_tokens", 0),
                    tokens_total=usage_data.get("total_tokens", 0),
                    error_message=error_message,
                )
                db.add(log)
                db.commit()

                # 累加 Token 使用量
                if usage_data["total_tokens"] > 0:
                    QuotaMonitor.add_usage(model.id, usage_data["total_tokens"])
            finally:
                db.close()
        except Exception as e:
            print(f"[ERROR] Anthropic SDK 流式日志记录异常：{e}")


async def _conversion_anthropic_to_openai_stream_with_logging(
    model,
    request_data: dict,
    requested_model: Optional[str],
    client_ip: Optional[str],
    user_agent: Optional[str],
    max_tokens: int,
    api_base_override: Optional[str] = None,
    tools: Optional[List[Dict]] = None,
):
    """转换模式流式请求：Anthropic -> OpenAI -> Anthropic

    将 Anthropic 格式请求转换为 OpenAI 格式，使用 OpenAI SDK 转发，
    然后将流式响应转换回 Anthropic 格式返回。
    """
    request_time = datetime.now()
    start_time = time.time()
    collected_content = []
    collected_tool_calls = []
    usage_data = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    error_message = None
    finish_reason = None

    try:
        # 使用 SDKGateway 进行 OpenAI 格式流式转发
        async for chunk in SDKGateway.stream_request(
            api_spec="openai",
            api_base=api_base_override if api_base_override else model.api_base,
            api_key=model.api_key,
            request_data=request_data,
            api_path=model.api_path,
        ):
            # 将 OpenAI 流式响应转换为 Anthropic 格式
            if chunk.startswith("data: "):
                try:
                    data_str = chunk[6:].strip()
                    if data_str and data_str != "[DONE]":
                        openai_chunk = json.loads(data_str)

                        # 转换为 Anthropic 格式的事件
                        anthropic_event = _convert_openai_chunk_to_anthropic_event(
                            openai_chunk, collected_content, collected_tool_calls
                        )

                        if anthropic_event:
                            yield f"event: {anthropic_event['type']}\ndata: {json.dumps(anthropic_event, ensure_ascii=False)}\n\n"

                        # 收集 usage 信息
                        if openai_chunk.get("usage"):
                            usage = openai_chunk["usage"]
                            usage_data["input_tokens"] = usage.get("prompt_tokens", 0)
                            usage_data["output_tokens"] = usage.get("completion_tokens", 0)
                            usage_data["total_tokens"] = usage.get("total_tokens", 0)

                    elif data_str == "[DONE]":
                        # 发送 message_stop 事件
                        yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

                except Exception as e:
                    print(f"[WARN] 转换流式数据失败：{e}")
                    pass
            else:
                # 直接转发非 data: 开头的 chunk（如 event:）
                yield chunk

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        try:
            response_time = datetime.now()
            duration_ms = (time.time() - start_time) * 1000

            db = SessionLocal()
            try:
                log = OperationLog(
                    log_type=1,
                    model_id=model.id,
                    log_content=json.dumps({
                        "model": requested_model or "auto",
                        "actual_model": model.model_name,
                        "api": "openai_sdk_with_anthropic_conversion",
                        "status": "success" if not error_message else "error",
                        "duration_ms": duration_ms,
                        "finish_reason": finish_reason,
                    }),
                    status=0 if error_message else 1,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    client_ip=client_ip or "",
                    user_agent=user_agent or "",
                    request_model=requested_model or "auto",
                    actual_model=model.model_name,
                    vendor=model.vendor,
                    tokens_prompt=usage_data.get("input_tokens", 0),
                    tokens_completion=usage_data.get("output_tokens", 0),
                    tokens_total=usage_data.get("total_tokens", 0),
                    error_message=error_message,
                )
                db.add(log)
                db.commit()

                if usage_data["total_tokens"] > 0:
                    QuotaMonitor.add_usage(model.id, usage_data["total_tokens"])
            finally:
                db.close()
        except Exception as e:
            print(f"[ERROR] 转换模式流式日志记录异常：{e}")


def _convert_openai_chunk_to_anthropic_event(
    openai_chunk: Dict,
    collected_content: List[str],
    collected_tool_calls: List[Dict],
) -> Optional[Dict]:
    """将 OpenAI 流式 chunk 转换为 Anthropic 格式事件

    OpenAI chunk 结构:
    {
        "id": "chatcmpl-xxx",
        "choices": [{"delta": {"role": "assistant", "content": "..."}, "finish_reason": None}],
        "created": 1234567890,
        "model": "gpt-4",
        "object": "chat.completion.chunk"
    }

    返回 Anthropic 事件:
    - message_start
    - content_block_start
    - content_block_delta (type: text_delta)
    - content_block_stop
    - message_delta (with stop_reason and usage)
    - message_stop
    """
    if not openai_chunk.get("choices"):
        return None

    choice = openai_chunk["choices"][0]
    delta = choice.get("delta", {})
    finish_reason = choice.get("finish_reason")

    events = []

    # 处理角色消息（message_start）
    if delta.get("role") == "assistant":
        return {
            "type": "message_start",
            "message": {
                "id": f"msg_{openai_chunk.get('id', 'unknown')}",
                "role": "assistant",
                "content": [],
                "model": openai_chunk.get("model", "unknown"),
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
        }

    # 处理文本内容
    if delta.get("content"):
        collected_content.append(delta["content"])
        return {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "text_delta",
                "text": delta["content"]
            }
        }

    # 处理 tool_calls
    if delta.get("tool_calls"):
        for tc in delta["tool_calls"]:
            tool_call = {
                "index": len(collected_tool_calls),
                "id": tc.get("id", f"toolu_{len(collected_tool_calls)}"),
                "type": "tool_use",
                "name": tc.get("function", {}).get("name", ""),
                "input": {}
            }
            collected_tool_calls.append(tool_call)

            # 返回 tool_use 事件
            return {
                "type": "content_block_start",
                "index": tool_call["index"],
                "content_block": {
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    "input": {}
                }
            }

    # 处理 finish_reason
    if finish_reason:
        anthropic_stop_reason = _convert_openai_finish_reason_to_anthropic(finish_reason)
        return {
            "type": "message_delta",
            "delta": {
                "stop_reason": anthropic_stop_reason,
                "stop_sequence": None
            },
            "usage": {
                "output_tokens": 0  # 实际值会在后续更新
            }
        }

    return None


def _convert_openai_finish_reason_to_anthropic(openai_reason: str) -> str:
    """将 OpenAI finish_reason 转换为 Anthropic stop_reason"""
    mapping = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "content_filter": "end_turn",
        "function_call": "tool_use",
    }
    return mapping.get(openai_reason, "end_turn")


def _convert_openai_to_anthropic_response(openai_response: Dict) -> Dict:
    """将 OpenAI 响应转换为 Anthropic 格式

    OpenAI 响应结构:
    {
        "id": "chatcmpl-xxx",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "...", "tool_calls": [...]},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    }

    返回 Anthropic 格式:
    {
        "id": "msg_xxx",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "..."}],
        "model": "claude-xxx",
        "stop_reason": "end_turn",
        "stop_sequence": null,
        "usage": {"input_tokens": 10, "output_tokens": 20}
    }
    """
    # 提取内容
    content_blocks = []
    tool_use_blocks = []

    if openai_response.get("choices"):
        choice = openai_response["choices"][0]
        message = choice.get("message", {})

        # 添加文本内容
        content = message.get("content", "")
        if content:
            content_blocks.append({
                "type": "text",
                "text": content
            })

        # 转换 tool_calls 为 tool_use
        tool_calls = message.get("tool_calls") or []
        for tc in tool_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                try:
                    input_args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    input_args = {}

                tool_use_blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", f"toolu_{len(tool_use_blocks)}"),
                    "name": func.get("name", ""),
                    "input": input_args
                })

        # 合并内容块（先文本后工具）
        content_blocks.extend(tool_use_blocks)

    # 转换 finish_reason
    finish_reason = "stop"
    if openai_response.get("choices"):
        finish_reason = openai_response["choices"][0].get("finish_reason", "stop")
    stop_reason = _convert_openai_finish_reason_to_anthropic(finish_reason)

    # 提取 usage
    usage = openai_response.get("usage", {})

    # 构建 Anthropic 格式响应
    return {
        "id": f"msg_{openai_response.get('id', 'unknown')}",
        "type": "message",
        "role": "assistant",
        "content": content_blocks,
        "model": openai_response.get("model", "unknown"),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0)
        }
    }

