import json
import time
import httpx
from typing import AsyncGenerator, Dict, Any, List


class GatewayCore:
    """网关核心服务 - 请求转发与响应映射"""

    # 厂商API配置模板
    VENDOR_CONFIGS = {
        "openai": {
            "name": "OpenAI",
            "api_base": "https://api.openai.com/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "qwen": {
            "name": "通义千问",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "zhipu": {
            "name": "智谱 AI",
            "api_base": "https://open.bigmodel.cn/api/paas/v4",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "spark": {
            "name": "讯飞星火",
            "api_base": "https://spark-api.xf-yun.com",
            "api_path": "/v3.5/chat",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "spark",
        },
        "spark_websocket": {
            "name": "讯飞星火 (WebSocket)",
            "api_base": "wss://spark-api.xf-yun.com",
            "api_path": "/v3.5/chat",
            "auth_header": "Authorization",
            "auth_format": "HMAC",
            "stream_support": True,
            "api_spec": "spark_ws",
            "need_sign": True,
        },
        "hunyuan": {
            "name": "腾讯混元",
            "api_base": "https://api.hunyuan.cloud.tencent.com/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "qwen_official": {
            "name": "通义千问 (官方)",
            "api_base": "https://dashscope.aliyuncs.com",
            "api_path": "/api/v1/services/aigc/text-generation/generation",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "qwen_official",
        },
        "doubao": {
            "name": "豆包",
            "api_base": "https://ark.cn-beijing.volces.com/api/v3",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "claude": {
            "name": "Claude",
            "api_base": "https://api.anthropic.com/v1",
            "api_path": "/messages",
            "auth_header": "x-api-key",
            "auth_format": "",
            "stream_support": True,
            "api_spec": "anthropic",
        },
        "gemini": {
            "name": "Gemini",
            "api_base": "https://generativelanguage.googleapis.com/v1beta",
            "api_path": "/models/gemini-pro:generateContent",
            "auth_header": "x-goog-api-key",
            "auth_format": "",
            "stream_support": False,
            "api_spec": "gemini",
        },
        "mistral": {
            "name": "Mistral AI",
            "api_base": "https://api.mistral.ai/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "perplexity": {
            "name": "Perplexity",
            "api_base": "https://api.perplexity.ai",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "groq": {
            "name": "Groq",
            "api_base": "https://api.groq.com/openai/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "ollama": {
            "name": "Ollama",
            "api_base": "http://localhost:11434",
            "api_path": "/v1/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "localai": {
            "name": "LocalAI",
            "api_base": "http://localhost:8080/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": False,
            "api_spec": "openai",
        },
        "lmstudio": {
            "name": "LM Studio",
            "api_base": "http://localhost:1234/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": False,
            "api_spec": "openai",
        },
        "vllm": {
            "name": "vLLM",
            "api_base": "http://localhost:8000/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "minimax": {
            "name": "MiniMax",
            "api_base": "https://api.minimax.io/v1/text",
            "api_path": "/chatcompletion_v2",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "deepseek": {
            "name": "DeepSeek",
            "api_base": "https://api.deepseek.com/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "moonshot": {
            "name": "月之暗面 (Moonshot)",
            "api_base": "https://api.moonshot.cn/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "stepfun": {
            "name": "阶跃星辰 (StepFun)",
            "api_base": "https://api.stepfun.com/v1",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "tongyi": {
            "name": "腾讯混元",
            "api_base": "https://hunyuan.cn-shanghai..tencentcloudapi.com/v1",
            "api_path": "/asr/chat-completion",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "openai",
        },
        "custom": {
            "name": "自定义",
            "api_base": "",
            "api_path": "",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True,
            "api_spec": "custom",
        },
    }

    # API 规范配置
    API_SPECS = {
        "openai": {
            "description": "OpenAI 兼容 API",
            "request_format": "openai",
            "response_format": "openai",
            "default_path": "/chat/completions",
        },
        "anthropic": {
            "description": "Anthropic Claude API",
            "request_format": "anthropic",
            "response_format": "anthropic",
            "default_path": "/messages",
        },
        "gemini": {
            "description": "Google Gemini API",
            "request_format": "gemini",
            "response_format": "gemini",
            "default_path": "/models/{model}:generateContent",
        },
        "custom": {
            "description": "完全自定义 API",
            "request_format": "custom",
            "response_format": "custom",
            "default_path": "",
        },
    }

    # OpenAI参数到各厂商参数的映射
    PARAM_MAPPING = {
        "openai": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "presence_penalty": "presence_penalty",
            "frequency_penalty": "frequency_penalty",
            "stop": "stop",
        },
        "qwen": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
        },
        "zhipu": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
        },
        "claude": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop",
        },
        "gemini": {
            "max_tokens": "maxOutputTokens",
            "temperature": "temperature",
            "top_p": "topP",
            "top_k": "topK",
            "stop": "stopSequences",
        },
        "spark": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_k": "top_k",
        },
        "doubao": {
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
        },
    }

    # 厂商特定的请求体构建器
    @classmethod
    def _build_vendor_request(cls, vendor: str, request_data: Dict) -> Dict:
        """根据厂商构建特定的请求体"""
        base_request = {
            "model": request_data.get("model"),
            "messages": request_data.get("messages", []),
        }

        # 复制标准参数
        for param in ["temperature", "max_tokens", "top_p", "stop", "stream"]:
            if param in request_data:
                base_request[param] = request_data[param]

        # 厂商特定处理
        config = cls.VENDOR_CONFIGS.get(vendor, {})

        # 如果是 OpenAI 兼容模式，直接使用标准格式
        if config.get("openai_compatible"):
            return request_data

        if vendor == "gemini":
            return cls._build_gemini_request(request_data)
        elif vendor == "claude":
            return cls._build_claude_request(request_data)
        elif vendor == "qwen":
            return cls._build_qwen_request(request_data)
        elif vendor in ["qwen_official"]:
            return cls._build_qwen_official_request(request_data)
        elif vendor == "spark":
            return cls._build_spark_request(request_data)

        return base_request

    @classmethod
    def _build_gemini_request(cls, request_data: Dict) -> Dict:
        """构建 Gemini 请求体"""
        contents = []
        system_instruction = None

        for msg in request_data.get("messages", []):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        request = {"contents": contents}

        if system_instruction:
            request["systemInstruction"] = system_instruction

        # 生成配置
        generation_config = {}
        if "temperature" in request_data:
            generation_config["temperature"] = request_data["temperature"]
        if "max_tokens" in request_data:
            generation_config["maxOutputTokens"] = request_data["max_tokens"]
        if "top_p" in request_data:
            generation_config["topP"] = request_data["top_p"]
        if "top_k" in request_data:
            generation_config["topK"] = request_data["top_k"]
        if "stop" in request_data:
            generation_config["stopSequences"] = (
                request_data["stop"]
                if isinstance(request_data["stop"], list)
                else [request_data["stop"]]
            )

        if generation_config:
            request["generationConfig"] = generation_config

        return request

    @classmethod
    def _build_claude_request(cls, request_data: Dict) -> Dict:
        """构建 Claude 请求体"""
        messages = request_data.get("messages", [])
        system_msg = None
        chat_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                chat_messages.append(msg)

        request = {
            "model": request_data.get("model"),
            "messages": chat_messages,
            "max_tokens": request_data.get("max_tokens", 4096),
        }

        if system_msg:
            request["system"] = system_msg
        if "temperature" in request_data:
            request["temperature"] = request_data["temperature"]
        if "top_p" in request_data:
            request["top_p"] = request_data["top_p"]
        if "stop" in request_data:
            request["stop_sequences"] = (
                request_data["stop"]
                if isinstance(request_data["stop"], list)
                else [request_data["stop"]]
            )

        return request

    @classmethod
    def _build_qwen_request(cls, request_data: Dict) -> Dict:
        """构建 Qwen OpenAI 兼容格式请求体"""
        messages = request_data.get("messages", [])

        # Qwen 使用 input 字段
        return {
            "model": request_data.get("model"),
            "input": {"messages": messages},
            "parameters": {
                "result_format": "message",
                "max_tokens": request_data.get("max_tokens", 1500),
                "temperature": request_data.get("temperature", 0.7),
                "top_p": request_data.get("top_p", 0.8),
            },
        }

    @classmethod
    def _build_qwen_official_request(cls, request_data: Dict) -> Dict:
        """构建 Qwen 官方格式请求体"""
        messages = request_data.get("messages", [])

        # 构建 Qwen 官方格式
        return {
            "model": request_data.get("model"),
            "input": {
                "messages": [
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                    for msg in messages
                ]
            },
            "parameters": {
                "result_format": "message",
                "max_output_tokens": request_data.get("max_tokens", 1500),
                "temperature": request_data.get("temperature", 0.7),
                "top_p": request_data.get("top_p", 0.8),
            },
        }

    @classmethod
    def _build_spark_request(cls, request_data: Dict) -> Dict:
        """构建讯飞星火官方格式请求体"""
        messages = request_data.get("messages", [])

        # 构建星火格式的消息
        text = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            text.append({"role": role, "content": content})

        return {
            "header": {
                "app_id": "",  # 需要从配置获取
                "uid": "gateway-user",
            },
            "parameter": {
                "chat": {
                    "domain": request_data.get("model", "generalv3.5"),
                    "temperature": request_data.get("temperature", 0.5),
                    "max_tokens": request_data.get("max_tokens", 2048),
                    "top_k": 4,
                }
            },
            "payload": {"message": {"text": text}},
        }

    @classmethod
    def _build_ollama_request(cls, request_data: Dict) -> Dict:
        """构建 Ollama 请求体"""
        # Ollama 的 /api/chat 端点格式
        messages = request_data.get("messages", [])

        # Ollama 的 messages 格式与 OpenAI 兼容
        # 但需要确保 role 只能是 user 或 assistant
        ollama_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Ollama 只支持 user 和 assistant，system 转为 user
            if role == "system":
                ollama_messages.append(
                    {"role": "user", "content": f"System: {content}"}
                )
            else:
                ollama_messages.append({"role": role, "content": content})

        request = {
            "model": request_data.get("model"),
            "messages": ollama_messages,
            "stream": request_data.get("stream", False),
        }

        # 可选参数
        options = {}
        if "temperature" in request_data:
            options["temperature"] = request_data["temperature"]
        if "max_tokens" in request_data:
            options["num_predict"] = request_data["max_tokens"]
        if "top_p" in request_data:
            options["top_p"] = request_data["top_p"]
        if "stop" in request_data:
            options["stop"] = (
                request_data["stop"]
                if isinstance(request_data["stop"], list)
                else [request_data["stop"]]
            )

        if options:
            request["options"] = options

        return request

    @classmethod
    async def test_connectivity(
        cls, vendor: str, api_base: str, api_key: str, model_name: str = None
    ) -> bool:
        """测试模型连通性"""
        try:
            if not api_base.startswith(("http://", "https://")):
                print(
                    f"连通性测试失败: API Base URL 格式错误，应以 http:// 或 https:// 开头"
                )
                return False

            config = cls.VENDOR_CONFIGS.get(vendor, {})
            headers = cls._build_headers(vendor, api_key, config)

            test_request = cls._build_test_request(vendor, model_name)
            api_path = config.get("api_path", "/v1/chat/completions")

            api_base_clean = api_base.rstrip("/")
            if api_base_clean.endswith("/v1"):
                api_base_clean = api_base_clean[:-3]
            url = f"{api_base_clean}{api_path}"

            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=False
            ) as client:
                response = await client.post(url, json=test_request, headers=headers)
                print(f"[DEBUG] Test response status: {response.status_code}")
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:
                    # 429 表示 API 可达但额度限制（如余额不足），视为连通
                    print(f"[DEBUG] API 返回 429，视为连通（可能是余额不足）")
                    return True
                elif 400 <= response.status_code < 500:
                    print(
                        f"[DEBUG] Client error {response.status_code}: {response.text[:200]}"
                    )
                    return False
                else:
                    return True

        except Exception as e:
            print(f"连通性测试失败: {e}")
            return False

    @classmethod
    async def fetch_available_models(
        cls, vendor: str, api_base: str, api_key: str
    ) -> Dict[str, Any]:
        """获取厂商可用模型列表"""
        try:
            if not api_base.startswith(("http://", "https://")):
                return {
                    "success": False,
                    "message": "API Base URL 格式错误",
                    "models": [],
                }

            config = cls.VENDOR_CONFIGS.get(vendor, {})

            # 对于有标准接口的厂商，尝试调用API获取
            if vendor == "openai":
                return await cls._fetch_openai_models(api_base, api_key)
            elif vendor == "gemini":
                return await cls._fetch_gemini_models(api_base, api_key)
            elif vendor in ["groq"]:
                return await cls._fetch_openai_compatible_models(
                    vendor, api_base, api_key
                )
            elif vendor == "ollama":
                return await cls._fetch_ollama_models(api_base)
            else:
                # 其他厂商使用内置列表
                return {
                    "success": True,
                    "message": f"{vendor} 暂不支持自动获取模型列表",
                    "models": cls._get_builtin_models(vendor),
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"获取模型列表失败: {str(e)}",
                "models": [],
            }

    @classmethod
    async def _fetch_openai_models(cls, api_base: str, api_key: str) -> Dict[str, Any]:
        """获取 OpenAI 兼容格式的模型列表"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            api_base_clean = api_base.rstrip("/")
            if not api_base_clean.endswith("/v1"):
                api_base_clean = f"{api_base_clean}/v1"

            url = f"{api_base_clean}/models"

            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=False
            ) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("data", []):
                        model_id = model.get("id", "")
                        # 过滤出对话模型
                        if any(
                            keyword in model_id.lower()
                            for keyword in [
                                "gpt",
                                "claude",
                                "qwen",
                                "glm",
                                "llama",
                                "mistral",
                                "gemini",
                            ]
                        ):
                            models.append(
                                {
                                    "id": model_id,
                                    "name": model_id,
                                    "description": model.get("description", ""),
                                }
                            )

                    return {
                        "success": True,
                        "message": f"成功获取 {len(models)} 个模型",
                        "models": models,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"API返回错误: {response.status_code}",
                        "models": [],
                    }

        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}", "models": []}

    @classmethod
    async def _fetch_gemini_models(cls, api_base: str, api_key: str) -> Dict[str, Any]:
        """获取 Gemini 模型列表"""
        try:
            api_base_clean = api_base.rstrip("/")
            url = f"{api_base_clean}/v1beta/models?key={api_key}"

            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=False
            ) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        model_name = model.get("name", "").replace("models/", "")
                        if "gemini" in model_name.lower():
                            models.append(
                                {
                                    "id": model_name,
                                    "name": model_name,
                                    "description": model.get("description", ""),
                                }
                            )

                    return {
                        "success": True,
                        "message": f"成功获取 {len(models)} 个模型",
                        "models": models,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"API返回错误: {response.status_code}",
                        "models": [],
                    }

        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}", "models": []}

    @classmethod
    async def _fetch_openai_compatible_models(
        cls, vendor: str, api_base: str, api_key: str
    ) -> Dict[str, Any]:
        """获取 OpenAI 兼容格式的模型列表"""
        return await cls._fetch_openai_models(api_base, api_key)

    @classmethod
    async def _fetch_ollama_models(cls, api_base: str) -> Dict[str, Any]:
        """获取 Ollama 本地模型列表"""
        try:
            # Ollama 的模型列表 API 是 /api/tags
            # 需要从 API Base 中提取主机地址
            from urllib.parse import urlparse

            # 确保 URL 有协议头
            if not api_base.startswith(("http://", "https://")):
                api_base = "http://" + api_base

            parsed = urlparse(api_base)
            host = parsed.netloc

            # 如果 netloc 为空，可能是没有协议头的情况
            if not host:
                host = parsed.path.split("/")[0]

            # 构建 Ollama tags API URL
            url = f"http://{host}/api/tags"

            print(f"[DEBUG] 获取 Ollama 模型列表: {url}")

            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=False
            ) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        model_name = model.get("name", "")
                        models.append(
                            {
                                "id": model_name,
                                "name": model_name,
                                "description": f"Size: {model.get('size', 'unknown')}",
                            }
                        )

                    return {
                        "success": True,
                        "message": f"成功获取 {len(models)} 个本地模型",
                        "models": models,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Ollama API返回错误: {response.status_code}",
                        "models": [],
                    }

        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}", "models": []}

    @classmethod
    def _get_builtin_models(cls, vendor: str) -> List[Dict[str, Any]]:
        """获取内置模型列表"""
        vendor_models = {
            "openai": [
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "description": "高性价比通用模型",
                },
                {"id": "gpt-4", "name": "GPT-4", "description": "高级推理能力"},
                {"id": "gpt-4o", "name": "GPT-4o", "description": "最新多模态模型"},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "轻量快速"},
            ],
            "qwen": [
                {
                    "id": "qwen-turbo",
                    "name": "通义千问 Turbo",
                    "description": "高性价比",
                },
                {"id": "qwen-plus", "name": "通义千问 Plus", "description": "增强版本"},
                {"id": "qwen-max", "name": "通义千问 Max", "description": "最强性能"},
            ],
            "zhipu": [
                {"id": "glm-4", "name": "GLM-4", "description": "智谱最强模型"},
                {"id": "glm-4v", "name": "GLM-4V", "description": "多模态版本"},
                {"id": "glm-3-turbo", "name": "GLM-3 Turbo", "description": "高性价比"},
            ],
            "spark": [
                {"id": "spark-v3.1", "name": "星火 V3.1", "description": "最新版本"},
                {"id": "spark-v3.5", "name": "星火 V3.5", "description": "增强版本"},
            ],
            "doubao": [
                {
                    "id": "Doubao-pro-32k",
                    "name": "豆包 Pro 32K",
                    "description": "32K上下文",
                },
                {
                    "id": "Doubao-pro-128k",
                    "name": "豆包 Pro 128K",
                    "description": "128K上下文",
                },
            ],
            "claude": [
                {
                    "id": "claude-sonnet-4-20250514",
                    "name": "Claude Sonnet 4",
                    "description": "平衡性能",
                },
                {
                    "id": "claude-opus-4-20250514",
                    "name": "Claude Opus 4",
                    "description": "最强性能",
                },
                {
                    "id": "claude-haiku-3-20250514",
                    "name": "Claude Haiku 3",
                    "description": "快速响应",
                },
            ],
            "gemini": [
                {
                    "id": "gemini-1.5-pro",
                    "name": "Gemini 1.5 Pro",
                    "description": "高级版本",
                },
                {
                    "id": "gemini-1.5-flash",
                    "name": "Gemini 1.5 Flash",
                    "description": "快速版本",
                },
                {"id": "gemini-pro", "name": "Gemini Pro", "description": "通用版本"},
            ],
            "mistral": [
                {
                    "id": "mistral-large",
                    "name": "Mistral Large",
                    "description": "最强版本",
                },
                {
                    "id": "mistral-medium",
                    "name": "Mistral Medium",
                    "description": "中等版本",
                },
                {
                    "id": "mistral-small",
                    "name": "Mistral Small",
                    "description": "轻量版本",
                },
            ],
            "groq": [
                {
                    "id": "llama3-70b-8192",
                    "name": "Llama 3 70B",
                    "description": "Llama3 70B",
                },
                {
                    "id": "llama3-8b-8192",
                    "name": "Llama 3 8B",
                    "description": "Llama3 8B",
                },
                {
                    "id": "mixtral-8x7b-32768",
                    "name": "Mixtral 8x7b",
                    "description": "Mixtral",
                },
            ],
            "ollama": [
                {"id": "llama3", "name": "Llama 3", "description": "Meta Llama 3"},
                {
                    "id": "llama3.1",
                    "name": "Llama 3.1",
                    "description": "Meta Llama 3.1",
                },
                {"id": "qwen2", "name": "Qwen 2", "description": "通义千问2"},
                {"id": "mistral", "name": "Mistral", "description": "Mistral 7B"},
            ],
            "localai": [
                {"id": "llama-2-7b", "name": "Llama 2 7B", "description": "Llama 2"},
                {"id": "mistral-7b", "name": "Mistral 7B", "description": "Mistral"},
            ],
            "lmstudio": [
                {"id": "llama-3-8b", "name": "Llama 3 8B", "description": "Llama 3"},
                {"id": "mistral-7b", "name": "Mistral 7B", "description": "Mistral"},
            ],
            "vllm": [
                {"id": "llama-2-7b", "name": "Llama 2 7B", "description": "Llama 2"},
                {"id": "qwen-14b", "name": "Qwen 14B", "description": "通义千问14B"},
            ],
        }

        models = vendor_models.get(vendor, [])
        return [
            {"id": m["id"], "name": m["name"], "description": m["description"]}
            for m in models
        ]

    @classmethod
    async def sync_request(
        cls, vendor: str, api_base: str, api_key: str, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步请求转发"""
        config = cls.VENDOR_CONFIGS.get(vendor, {})
        headers = cls._build_headers(vendor, api_key, config)

        # 参数映射
        mapped_request = cls._map_params(vendor, request_data)

        # 构建 URL，避免路径重复
        api_base_clean = api_base.rstrip("/")
        api_path = config.get("api_path", "/v1/chat/completions")

        # 检查 api_base 是否已经包含 api_path 的部分路径
        # 例如 api_base="https://example.com/v1" 且 api_path="/v1/chat/completions"
        url = api_base_clean
        if api_path.startswith("/v1") and api_base_clean.endswith("/v1"):
            # 去掉重复的 /v1
            url = f"{api_base_clean}{api_path[3:]}"
        else:
            url = f"{api_base_clean}{api_path}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=mapped_request, headers=headers)

            if response.status_code != 200:
                raise Exception(
                    f"API请求失败: {response.status_code} - {response.text}"
                )

            response_data = response.json()

            # 响应标准化为OpenAI格式
            return cls._standardize_response(vendor, response_data)

    @classmethod
    async def stream_request(
        cls, vendor: str, api_base: str, api_key: str, request_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式请求转发"""
        config = cls.VENDOR_CONFIGS.get(vendor, {})
        headers = cls._build_headers(vendor, api_key, config)

        # 参数映射
        mapped_request = cls._map_params(vendor, request_data)

        # 构建 URL，避免路径重复
        api_base_clean = api_base.rstrip("/")
        api_path = config.get("api_path", "/v1/chat/completions")

        # 检查 api_base 是否已经包含 api_path 的部分路径
        if api_path.startswith("/v1") and api_base_clean.endswith("/v1"):
            # 去掉重复的 /v1
            url = f"{api_base_clean}{api_path[3:]}"
        else:
            url = f"{api_base_clean}{api_path}"

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST", url, json=mapped_request, headers=headers
            ) as response:
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': '请求失败'})}\n\n"
                    return

                async for chunk in response.aiter_lines():
                    if chunk:
                        # 转换为OpenAI SSE格式
                        standardized = cls._standardize_stream_chunk(vendor, chunk)
                        if standardized:
                            yield standardized

    @classmethod
    def _build_headers(cls, vendor: str, api_key: str, config: Dict) -> Dict:
        """构建请求头"""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        auth_header = config.get("auth_header", "Authorization")
        auth_format = config.get("auth_format", "Bearer")

        if auth_header == "Authorization":
            headers[auth_header] = f"{auth_format} {api_key}"
        else:
            headers[auth_header] = api_key

        # 厂商特定请求头
        if vendor == "claude":
            headers["anthropic-version"] = "2023-06-01"
            headers["anthropic-dangerous-direct-browser-access"] = "true"

        if vendor == "gemini":
            headers["Content-Type"] = "application/json"

        return headers

    @classmethod
    def _build_test_request(cls, vendor: str, model_name: str = None) -> Dict:
        """构建测试请求"""
        use_model_name = (
            model_name
            if model_name
            else ("llama3.2" if vendor == "ollama" else "gpt-3.5-turbo")
        )

        if vendor == "claude":
            return {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}],
            }
        elif vendor == "ollama":
            return {
                "model": use_model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "options": {"num_predict": 10},
            }
        else:
            return {
                "model": use_model_name,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            }

    @classmethod
    def _map_params(cls, vendor: str, request_data: Dict) -> Dict:
        """参数映射 - 将OpenAI参数转换为目标厂商格式"""
        # 使用厂商特定的构建器
        return cls._build_vendor_request(vendor, request_data)

    @classmethod
    def _standardize_response(cls, vendor: str, response_data: Dict) -> Dict:
        """响应标准化 - 将厂商响应转换为OpenAI格式"""
        # 根据厂商使用特定的解析器
        config = cls.VENDOR_CONFIGS.get(vendor, {})

        # 如果是 OpenAI 兼容模式，直接返回原始响应
        if config.get("openai_compatible"):
            return response_data

        if vendor == "gemini":
            return cls._parse_gemini_response(response_data)
        elif vendor == "claude":
            return cls._parse_claude_response(response_data)
        elif vendor == "qwen":
            return cls._parse_qwen_response(response_data)
        elif vendor == "qwen_official":
            return cls._parse_qwen_official_response(response_data)
        elif vendor == "spark":
            return cls._parse_spark_response(response_data)
        else:
            return cls._parse_openai_compatible_response(response_data)

    @classmethod
    def _parse_openai_compatible_response(cls, response_data: Dict) -> Dict:
        """解析 OpenAI 兼容格式的响应"""
        standardized = {
            "id": response_data.get("id", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": response_data.get("created", int(time.time())),
            "model": response_data.get("model", "unknown"),
            "choices": [],
            "usage": response_data.get(
                "usage",
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            ),
        }

        # 处理choices
        if "choices" in response_data:
            for choice in response_data["choices"]:
                message = choice.get("message", {})
                standardized["choices"].append(
                    {
                        "index": choice.get("index", 0),
                        "message": {
                            "role": message.get("role", "assistant"),
                            "content": message.get("content", ""),
                        },
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                )

        return standardized

    @classmethod
    def _parse_gemini_response(cls, response_data: Dict) -> Dict:
        """解析 Gemini 响应为 OpenAI 格式"""
        candidates = response_data.get("candidates", [])
        if not candidates:
            return {
                "id": f"chatcmpl-{id(response_data)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "gemini",
                "choices": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [{}])
        text = parts[0].get("text", "") if parts else ""

        usage_metadata = response_data.get("usageMetadata", {})

        return {
            "id": f"chatcmpl-{id(response_data)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gemini",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": text,
                    },
                    "finish_reason": candidate.get("finishReason", "stop").lower(),
                }
            ],
            "usage": {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0),
            },
        }

    @classmethod
    def _parse_claude_response(cls, response_data: Dict) -> Dict:
        """解析 Claude 响应为 OpenAI 格式"""
        content_blocks = response_data.get("content", [])
        text = ""
        for block in content_blocks:
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = response_data.get("usage", {})

        return {
            "id": response_data.get("id", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": response_data.get("model", "claude"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": text,
                    },
                    "finish_reason": response_data.get("stop_reason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0)
                + usage.get("output_tokens", 0),
            },
        }

    @classmethod
    def _parse_qwen_response(cls, response_data: Dict) -> Dict:
        """解析 Qwen 响应为 OpenAI 格式"""
        output = response_data.get("output", {})
        choices_data = output.get("choices", [])

        if not choices_data:
            return {
                "id": response_data.get("request_id", f"chatcmpl-{id(response_data)}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": output.get("model", "qwen"),
                "choices": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        choice = choices_data[0]
        message = choice.get("message", {})
        usage = response_data.get("usage", {})

        return {
            "id": response_data.get("request_id", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": output.get("model", "qwen"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                    },
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    @classmethod
    def _parse_qwen_official_response(cls, response_data: Dict) -> Dict:
        """解析 Qwen 官方格式响应为 OpenAI 格式"""
        output = response_data.get("output", {})
        choices_data = output.get("choices", [])

        if not choices_data:
            return {
                "id": response_data.get("request_id", f"chatcmpl-{id(response_data)}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": output.get("model", "qwen"),
                "choices": [],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        choice = choices_data[0]
        message = choice.get("message", {})
        usage = response_data.get("usage", {})

        return {
            "id": response_data.get("request_id", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": output.get("model", "qwen"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                    },
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    @classmethod
    def _parse_spark_response(cls, response_data: Dict) -> Dict:
        """解析讯飞星火响应为 OpenAI 格式"""
        header = response_data.get("header", {})
        payload = response_data.get("payload", {})
        choices_data = payload.get("choices", {}).get("text", [])

        text = ""
        if choices_data:
            text = choices_data[0].get("content", "")

        return {
            "id": header.get("sid", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": response_data.get("header", {})
            .get("skill", {})
            .get("name", "spark"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }

    @classmethod
    def _parse_ollama_response(cls, response_data: Dict) -> Dict:
        """解析 Ollama 响应为 OpenAI 格式"""
        message = response_data.get("message", {})

        return {
            "id": f"chatcmpl-{id(response_data)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": response_data.get("model", "ollama"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                    },
                    "finish_reason": "stop"
                    if response_data.get("done", True)
                    else None,
                }
            ],
            "usage": {
                "prompt_tokens": response_data.get("prompt_eval_count", 0),
                "completion_tokens": response_data.get("eval_count", 0),
                "total_tokens": response_data.get("prompt_eval_count", 0)
                + response_data.get("eval_count", 0),
            },
        }

    @classmethod
    def _standardize_stream_chunk(cls, vendor: str, chunk: str) -> str:
        """流式响应块标准化"""
        if not chunk.startswith("data:"):
            return None

        data = chunk[5:].strip()

        if data == "[DONE]":
            return "data: [DONE]\n\n"

        try:
            data_obj = json.loads(data)

            # 转换为OpenAI SSE格式
            standardized = {
                "id": data_obj.get("id", f"chatcmpl-{id(data_obj)}"),
                "object": "chat.completion.chunk",
                "created": data_obj.get("created", 0),
                "model": data_obj.get("model", "unknown"),
                "choices": data_obj.get("choices", []),
            }

            return f"data: {json.dumps(standardized)}\n\n"

        except json.JSONDecodeError:
            return None
