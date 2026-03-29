"""
基于官方 SDK 的网关服务模块

使用 OpenAI 和 Anthropic 官方 SDK 进行请求转发，实现完整的 API 格式透传
"""
import json
import time
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

# 导入 SDK
try:
    from openai import AsyncOpenAI
    from anthropic import AsyncAnthropic
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("[WARN] OpenAI 或 Anthropic SDK 未安装，请运行：pip install openai anthropic")

# 导入调试日志
from services.debug_logger import log_layer, is_enabled


class SDKGateway:
    """基于官方 SDK 的网关核心"""

    @classmethod
    async def stream_request(
        cls,
        api_spec: str,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
        api_path: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式请求转发

        Args:
            api_spec: API 规范 (openai 或 anthropic)
            api_base: 基础 URL
            api_key: API 密钥
            request_data: 请求数据
            api_path: 可选的路径覆盖

        Yields:
            SSE 格式的响应数据
        """
        if not SDK_AVAILABLE:
            yield f"data: {json.dumps({'error': 'SDK 未安装'})}\n\n"
            return

        if api_spec == "anthropic":
            async for chunk in cls._anthropic_stream(api_base, api_key, request_data):
                yield chunk
        else:
            # 默认使用 OpenAI 兼容格式（包括 openai, qwen, zhipu 等）
            async for chunk in cls._openai_stream(api_base, api_key, request_data, api_path):
                yield chunk

    @classmethod
    async def sync_request(
        cls,
        api_spec: str,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
        api_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        同步请求转发

        Args:
            api_spec: API 规范 (openai 或 anthropic)
            api_base: 基础 URL
            api_key: API 密钥
            request_data: 请求数据
            api_path: 可选的路径覆盖

        Returns:
            标准化的响应字典
        """
        if not SDK_AVAILABLE:
            return {"error": "SDK 未安装"}

        if api_spec == "anthropic":
            return await cls._anthropic_sync(api_base, api_key, request_data)
        else:
            return await cls._openai_sync(api_base, api_key, request_data, api_path)

    @classmethod
    async def _openai_stream(
        cls,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
        api_path: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """OpenAI 兼容格式流式请求"""
        # 使用传入的 request_id 或生成新的（优先使用传入的以保持追踪一致性）
        request_id = request_data.get("_request_id", str(uuid.uuid4())[:8])

        try:
            # 构建 base_url
            base_url = api_base.rstrip("/")
            if api_path and api_path != "/chat/completions":
                # 如果有自定义路径，需要处理
                if not base_url.endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120.0,
            )

            # 确保 stream=True
            request_data["stream"] = True

            # 移除不支持的字段
            clean_request = cls._clean_openai_request(request_data)

            # L2 日志：记录网关输出（转发给厂商的请求）
            if is_enabled():
                log_layer("L2", {
                    "api_spec": "openai",
                    "url": base_url,
                    "request": clean_request,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            stream = await client.chat.completions.create(**clean_request)

            # 收集响应用于 L3 日志
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
                yield f"data: {chunk.model_dump_json()}\n\n"

            # L3 日志：记录厂商响应（最后一个 chunk 包含完整信息）
            if is_enabled() and chunks:
                last_chunk = chunks[-1]
                log_layer("L3", {
                    "api_spec": "openai",
                    "response": last_chunk.model_dump(),
                }, context={"request_id": request_id, "model": request_data.get("model")})

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_type = cls._classify_error(e)
            error_response = {
                "error": str(e),
                "error_type": error_type,
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"

    @classmethod
    async def _openai_sync(
        cls,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
        api_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """OpenAI 兼容格式同步请求"""
        # 使用传入的 request_id 或生成新的（优先使用传入的以保持追踪一致性）
        request_id = request_data.get("_request_id", str(uuid.uuid4())[:8])

        try:
            base_url = api_base.rstrip("/")
            if api_path and api_path != "/chat/completions":
                if not base_url.endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120.0,
            )

            # 确保 stream=False
            request_data["stream"] = False
            clean_request = cls._clean_openai_request(request_data)

            # L2 日志：记录网关输出（转发给厂商的请求）
            if is_enabled():
                log_layer("L2", {
                    "api_spec": "openai",
                    "url": base_url,
                    "request": clean_request,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            response = await client.chat.completions.create(**clean_request)
            response_dict = response.model_dump()

            # L3 日志：记录厂商原始响应
            if is_enabled():
                log_layer("L3", {
                    "api_spec": "openai",
                    "response": response_dict,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            return response_dict

        except Exception as e:
            error_type = cls._classify_error(e)
            return {
                "error": str(e),
                "error_type": error_type,
            }

    @classmethod
    async def _anthropic_stream(
        cls,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Anthropic 格式流式请求

        Anthropic SDK 流式事件类型：
        - message_start: 消息开始，包含初始 message 对象
        - content_block_start: 内容块开始
        - content_block_delta: 内容块增量（文本生成）
        - content_block_stop: 内容块结束
        - message_delta: 消息增量（包含 stop_reason 和 usage）
        - message_stop: 消息结束
        """
        # 使用传入的 request_id 或生成新的（优先使用传入的以保持追踪一致性）
        request_id = request_data.get("_request_id", str(uuid.uuid4())[:8])

        try:
            client = AsyncAnthropic(
                api_key=api_key,
                base_url=api_base.rstrip("/"),
                timeout=120.0,
            )

            # 提取消息和系统提示
            messages = request_data.get("messages", [])
            system = request_data.get("system")

            # 构建 Anthropic 格式请求
            create_kwargs = {
                "model": request_data.get("model", "claude-sonnet-4-20250514"),
                "messages": messages,
                "max_tokens": request_data.get("max_tokens", 1024),
            }

            if system:
                create_kwargs["system"] = system
            if "temperature" in request_data:
                create_kwargs["temperature"] = request_data["temperature"]
            if "top_p" in request_data:
                create_kwargs["top_p"] = request_data["top_p"]
            if "stop_sequences" in request_data:
                create_kwargs["stop_sequences"] = request_data["stop_sequences"]
            # 工具调用相关参数
            if "tools" in request_data:
                create_kwargs["tools"] = request_data["tools"]
            if "tool_choice" in request_data:
                create_kwargs["tool_choice"] = request_data["tool_choice"]
            if "metadata" in request_data:
                create_kwargs["metadata"] = request_data["metadata"]

            # L2 日志：记录网关输出（转发给厂商的请求）
            if is_enabled():
                log_layer("L2", {
                    "api_spec": "anthropic",
                    "url": api_base.rstrip("/"),
                    "request": create_kwargs,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            # 创建流式请求 - 使用 stream=True
            stream = await client.messages.create(**create_kwargs, stream=True)

            # 收集响应用于 L3 日志
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
                # 根据事件类型构建响应
                event_type = getattr(chunk, 'type', 'unknown')

                event_data = {
                    "type": event_type,
                }

                # 处理不同类型的 chunk
                if event_type == "message_start":
                    if hasattr(chunk, 'message') and chunk.message:
                        event_data["message"] = chunk.message.model_dump()

                elif event_type == "content_block_start":
                    if hasattr(chunk, 'index'):
                        event_data["index"] = chunk.index
                    if hasattr(chunk, 'content_block') and chunk.content_block:
                        event_data["content_block"] = chunk.content_block.model_dump()

                elif event_type == "content_block_delta":
                    if hasattr(chunk, 'index'):
                        event_data["index"] = chunk.index
                    if hasattr(chunk, 'delta') and chunk.delta:
                        event_data["delta"] = chunk.delta.model_dump()

                elif event_type == "content_block_stop":
                    if hasattr(chunk, 'index'):
                        event_data["index"] = chunk.index

                elif event_type == "message_delta":
                    if hasattr(chunk, 'delta') and chunk.delta:
                        event_data["delta"] = chunk.delta.model_dump()
                    if hasattr(chunk, 'usage') and chunk.usage:
                        event_data["usage"] = chunk.usage.model_dump()

                elif event_type == "message_stop":
                    pass

                yield f"event: {event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"

            # L3 日志：记录厂商响应（最后一个 chunk 包含完整信息）
            if is_enabled() and chunks:
                last_chunk = chunks[-1]
                log_layer("L3", {
                    "api_spec": "anthropic",
                    "response": last_chunk.model_dump() if hasattr(last_chunk, 'model_dump') else str(last_chunk),
                }, context={"request_id": request_id, "model": request_data.get("model")})

        except Exception as e:
            # 区分错误类型
            error_type = cls._classify_error(e)
            error_response = {
                "error": str(e),
                "error_type": error_type,
            }
            yield f"event: error\ndata: {json.dumps(error_response, ensure_ascii=False)}\n\n"

    @classmethod
    async def _anthropic_sync(
        cls,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Anthropic 格式同步请求"""
        # 使用传入的 request_id 或生成新的（优先使用传入的以保持追踪一致性）
        request_id = request_data.get("_request_id", str(uuid.uuid4())[:8])

        try:
            client = AsyncAnthropic(
                api_key=api_key,
                base_url=api_base.rstrip("/"),
                timeout=120.0,
            )

            # 提取消息和系统提示
            messages = request_data.get("messages", [])
            system = request_data.get("system")

            # 构建 Anthropic 格式请求
            create_kwargs = {
                "model": request_data.get("model", "claude-sonnet-4-20250514"),
                "messages": messages,
                "max_tokens": request_data.get("max_tokens", 1024),
            }

            if system:
                create_kwargs["system"] = system
            if "temperature" in request_data:
                create_kwargs["temperature"] = request_data["temperature"]
            if "top_p" in request_data:
                create_kwargs["top_p"] = request_data["top_p"]
            if "stop_sequences" in request_data:
                create_kwargs["stop_sequences"] = request_data["stop_sequences"]
            # 工具调用相关参数
            if "tools" in request_data:
                create_kwargs["tools"] = request_data["tools"]
            if "tool_choice" in request_data:
                create_kwargs["tool_choice"] = request_data["tool_choice"]
            if "metadata" in request_data:
                create_kwargs["metadata"] = request_data["metadata"]

            # L2 日志：记录网关输出（转发给厂商的请求）
            if is_enabled():
                log_layer("L2", {
                    "api_spec": "anthropic",
                    "url": api_base.rstrip("/"),
                    "request": create_kwargs,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            response = await client.messages.create(**create_kwargs)
            response_dict = response.model_dump()

            # L3 日志：记录厂商原始响应
            if is_enabled():
                log_layer("L3", {
                    "api_spec": "anthropic",
                    "response": response_dict,
                }, context={"request_id": request_id, "model": request_data.get("model")})

            return response_dict

        except Exception as e:
            error_type = cls._classify_error(e)
            return {
                "error": str(e),
                "error_type": error_type,
            }

    @staticmethod
    def _clean_openai_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """清理 OpenAI 请求，移除不支持的字段

        注意：thinking 参数仅部分厂商支持（如 DeepSeek R1），
        百炼、智谱等厂商不支持，需要在 router 层根据 vendor 移除。
        此处保留该字段，由上层决定是否需要过滤。
        """
        # 保留所有标准字段
        allowed_fields = {
            "model", "messages", "temperature", "top_p", "n", "stream",
            "stop", "max_tokens", "presence_penalty", "frequency_penalty",
            "logit_bias", "user", "seed", "logprobs", "top_logprobs",
            "response_format", "tools", "tool_choice", "parallel_tool_calls",
            "function_call", "functions", "reasoning_effort", "thinking"
        }

        clean = {}
        for key, value in data.items():
            if key in allowed_fields and value is not None:
                clean[key] = value

        return clean

    @staticmethod
    def _classify_error(e: Exception) -> str:
        """分类错误类型

        返回：
            - "authentication_error": 认证错误（API Key 无效等）
            - "quota_error": 配额错误（余额不足、配额耗尽等）
            - "rate_limit_error": 速率限制错误
            - "network_error": 网络错误（超时、连接失败等）
            - "api_error": API 错误（参数无效、服务器错误等）
            - "unknown_error": 未知错误
        """
        from openai import (
            AuthenticationError,
            PermissionDeniedError,
            RateLimitError,
            APITimeoutError,
            APIConnectionError,
            APIStatusError,
            BadRequestError,
        )
        from anthropic import (
            AuthenticationError as AnthropicAuthError,
            PermissionDeniedError as AnthropicPermissionError,
            RateLimitError as AnthropicRateLimitError,
            APITimeoutError as AnthropicTimeoutError,
            APIConnectionError as AnthropicConnectionError,
            APIStatusError as AnthropicStatusError,
            BadRequestError as AnthropicBadRequestError,
        )

        # OpenAI SDK 错误
        if isinstance(e, (AuthenticationError, PermissionDeniedError)):
            return "authentication_error"
        if isinstance(e, RateLimitError):
            if "quota" in str(e).lower() or "balance" in str(e).lower():
                return "quota_error"
            return "rate_limit_error"
        if isinstance(e, (APITimeoutError, APIConnectionError)):
            return "network_error"
        if isinstance(e, BadRequestError):
            return "api_error"
        if isinstance(e, APIStatusError):
            if e.status_code == 401:
                return "authentication_error"
            if e.status_code == 429:
                return "rate_limit_error"
            if e.status_code >= 500:
                return "api_error"

        # Anthropic SDK 错误
        if isinstance(e, (AnthropicAuthError, AnthropicPermissionError)):
            return "authentication_error"
        if isinstance(e, AnthropicRateLimitError):
            if "quota" in str(e).lower() or "balance" in str(e).lower():
                return "quota_error"
            return "rate_limit_error"
        if isinstance(e, (AnthropicTimeoutError, AnthropicConnectionError)):
            return "network_error"
        if isinstance(e, AnthropicBadRequestError):
            return "api_error"
        if isinstance(e, AnthropicStatusError):
            if e.status_code == 401:
                return "authentication_error"
            if e.status_code == 429:
                return "rate_limit_error"
            if e.status_code >= 500:
                return "api_error"

        # 默认未知错误
        return "unknown_error"
