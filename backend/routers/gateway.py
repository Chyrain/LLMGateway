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

        # 决定要尝试的模型列表
        if is_auto_mode:
            # auto 模式：尝试所有可用模型
            models_to_try = available_models
        else:
            # 指定具体模型：只试指定的模型
            # 优先选择 api_spec 匹配的模型（OpenAI 端点优先选择 openai 格式）
            print(f"[DEBUG] Looking for model: '{requested_model}'")
            print(
                f"[DEBUG] Available models: {[m.model_name for m in available_models]}"
            )
            target_model = next(
                (m for m in available_models if m.model_name == requested_model and m.api_spec == "openai"), None
            )
            # 如果没有找到 openai 格式的模型，尝试查找任意匹配的模型
            if not target_model:
                target_model = next(
                    (m for m in available_models if m.model_name == requested_model), None
                )
            print(f"[DEBUG] target_model found: {target_model}")
            if target_model:
                models_to_try = [target_model]
            else:
                # 指定模型不存在或不可用
                print(f"[DEBUG] Model not found, raising 404")
                raise HTTPException(
                    status_code=404,
                    detail=f"模型 '{requested_model}' 不存在或不可用",
                )

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

                response = await GatewayCore.sync_request(
                    model.vendor,
                    model.api_base,
                    model.api_key,
                    request_data,
                    model.api_path,
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
            models_to_try = available_models
        else:
            # 优先选择 api_spec 匹配的模型（Anthropic 端点优先选择 anthropic 格式）
            target_model = next(
                (m for m in available_models if m.model_name == requested_model and m.api_spec == "anthropic"), None
            )
            # 如果没有找到 anthropic 格式的模型，尝试查找任意匹配的模型
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
                # 根据 api_spec 决定请求构建方式
                api_spec = model.api_spec or "openai"
                use_anthropic_format = api_spec == "anthropic"

                if use_anthropic_format:
                    # 直接使用 Anthropic 格式，完整透传
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
                else:
                    # 转换为 OpenAI 格式（向后兼容）
                    def extract_text_content(content: Union[str, List[dict]]) -> str:
                        """从 content 中提取文本内容"""
                        if isinstance(content, str):
                            return content
                        elif isinstance(content, list):
                            text_parts = []
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    text_parts.append(item["text"])
                            return "".join(text_parts)
                        return str(content)

                    messages = []
                    if request.system:
                        system_content = extract_text_content(request.system)
                        messages.append({"role": "system", "content": system_content})
                    for msg in request.messages:
                        content = extract_text_content(msg.content)
                        messages.append({"role": msg.role, "content": content})

                    request_data = {
                        "model": model.model_name,
                        "messages": messages,
                        "stream": request.stream,
                    }
                    if request.temperature is not None:
                        request_data["temperature"] = request.temperature
                    if request.max_tokens is not None:
                        request_data["max_tokens"] = request.max_tokens
                    if request.top_p is not None:
                        request_data["top_p"] = request.top_p
                    if request.stop_sequences:
                        request_data["stop"] = request.stop_sequences
                    for key, value in request.model_extra.items():
                        if key not in request_data and value is not None:
                            request_data[key] = value


                # 流式响应 - 根据 api_spec 选择 SDK
                if request.stream:
                    if use_anthropic_format:
                        # 使用 Anthropic SDK 流式转发
                        return StreamingResponse(
                            _sdk_anthropic_stream_with_logging(
                                model,
                                request_data,
                                requested_model,
                                client_ip,
                                user_agent,
                                request.max_tokens or 1024,
                            ),
                            media_type="text/event-stream",
                            headers={
                                "Cache-Control": "no-cache",
                                "Connection": "keep-alive",
                                "anthropic-version": anthropic_version,
                            },
                        )
                    else:
                        # 使用 OpenAI 兼容格式流式转发
                        return StreamingResponse(
                            _anthropic_stream_with_logging(
                                model,
                                request_data,
                                requested_model,
                                client_ip,
                                user_agent,
                                request.max_tokens or 1024,
                            ),
                            media_type="text/event-stream",
                            headers={
                                "Cache-Control": "no-cache",
                                "Connection": "keep-alive",
                                "anthropic-version": anthropic_version,
                            },
                        )
                else:
                    # 非流式响应 - 根据 api_spec 选择 SDK
                    if use_anthropic_format:
                        # 使用 Anthropic SDK 转发
                        response = await SDKGateway.sync_request(
                            api_spec="anthropic",
                            api_base=model.api_base,
                            api_key=model.api_key,
                            request_data=request_data,
                        )
                    else:
                        # 使用 OpenAI 兼容格式转发
                        response = await GatewayCore.sync_request(
                            model.vendor,
                            model.api_base,
                            model.api_key,
                            request_data,
                            model.api_path,
                        )

                # 验证响应是否包含错误
                if "error" in response:
                    error_detail = response.get("error", "Unknown error")
                    error_type = response.get("error_type", "unknown_error")
                    raise ValueError(f"API 错误 ({error_type}): {error_detail}")

                # 验证响应（支持 text 和 tool_use 内容块）
                if use_anthropic_format:
                    # Anthropic 格式响应验证
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
                else:
                    # OpenAI 格式响应验证
                    choices = response.get("choices", [])
                    if not choices or not choices[0].get("message", {}).get("content", "").strip():
                        raise ValueError("模型返回空响应")

                # 成功：记录日志并返回响应
                response_time = datetime.now()
                duration_ms = (time.time() - start_time) * 1000
                
                # 根据 api_spec 处理响应
                if use_anthropic_format:
                    # Anthropic SDK 返回的已经是 Anthropic 格式，直接透传
                    response_content = ""
                    content_blocks = response.get("content", [])
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
                else:
                    # OpenAI 格式响应，需要转换为 Anthropic 格式
                    choices = response.get("choices", [])
                    response_content = choices[0].get("message", {}).get("content", "")
                    usage = response.get("usage", {})
                    response_json_str = json.dumps(response, ensure_ascii=False)

                    log = OperationLog(
                        log_type=1,
                        model_id=model.id,
                        log_content=json.dumps({
                            "model": requested_model or "auto",
                            "actual_model": model.model_name,
                            "status": "success",
                            "api": "anthropic",
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
                        response_content=response_json_str[:10000],
                        tokens_prompt=usage.get("prompt_tokens", 0),
                        tokens_completion=usage.get("completion_tokens", 0),
                        tokens_total=usage.get("total_tokens", 0),
                    )
                    db.add(log)
                    db.commit()

                    try:
                        QuotaMonitor.add_usage_from_response(model.id, response)
                    except:
                        pass

                    stop_reason = "end_turn"
                    if choices and len(choices) > 0:
                        finish_reason = choices[0].get("finish_reason")
                        if finish_reason == "stop":
                            stop_reason = "end_turn"
                        elif finish_reason == "length":
                            stop_reason = "max_tokens"
                        elif finish_reason == "tool_calls":
                            stop_reason = "tool_use"
                        elif finish_reason == "content_filter":
                            stop_reason = "end_turn"
                        elif finish_reason:
                            stop_reason = finish_reason

                    stop_sequence = response.get("stop_sequence")

                    return {
                        "id": f"msg_{int(time.time() * 1000)}",
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": response_content}],
                        "model": model.model_name,
                        "stop_reason": stop_reason,
                        "stop_sequence": stop_sequence,
                        "usage": {
                            "input_tokens": usage.get("prompt_tokens", 0),
                            "output_tokens": usage.get("completion_tokens", 0),
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
):
    """Anthropic SDK 流式请求包装器，用于记录日志

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
            api_base=model.api_base,
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

