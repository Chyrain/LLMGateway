import json
import httpx
from typing import AsyncGenerator, Dict, Any

class GatewayCore:
    """网关核心服务 - 请求转发与响应映射"""
    
    # 厂商API配置模板
    VENDOR_CONFIGS = {
        "openai": {
            "api_base": "https://api.openai.com",
            "api_path": "/v1/chat/completions",
            "stream_path": "/v1/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "qwen": {
            "api_base": "https://dashscope.aliyuncs.com",
            "api_path": "/api/v1/services/aigc/text-generation/generation",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "zhipu": {
            "api_base": "https://open.bigmodel.cn",
            "api_path": "/api/llm/v3.5/chatcompletions_pro",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "spark": {
            "api_base": "https://spark-api.xf-yun.com",
            "api_path": "/v3.1/chat",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "doubao": {
            "api_base": "https://ark.cn-beijing.volces.com",
            "api_path": "/api/v3/bots/chat_sessions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "claude": {
            "api_base": "https://api.anthropic.com",
            "api_path": "/v1/messages",
            "auth_header": "x-api-key",
            "auth_format": "",
            "stream_support": True
        },
        "gemini": {
            "api_base": "https://generativelanguage.googleapis.com",
            "api_path": "/v1beta/models/gemini-pro:generateContent",
            "auth_header": "x-goog-api-key",
            "auth_format": "",
            "stream_support": False
        },
        "mistral": {
            "api_base": "https://api.mistral.ai",
            "api_path": "/v1/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer",
            "stream_support": True
        },
        "perplexity": {
            "api_base": "https://api.perplexity.ai",
            "api_path": "/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer"
        },
        "groq": {
            "api_base": "https://api.groq.com",
            "api_path": "/openai/v1/chat/completions",
            "auth_header": "Authorization",
            "auth_format": "Bearer"
        }
    }
    
    # OpenAI参数到各厂商参数的映射
    PARAM_MAPPING = {
        "openai": {
            "max_tokens": "max_tokens"
        },
        "qwen": {
            "max_tokens": "max_output_tokens",
            "temperature": "temperature"
        },
        "zhipu": {
            "max_tokens": "max_output_tokens",
            "temperature": "temperature"
        },
        "claude": {
            "max_tokens": "max_tokens",
            "temperature": "temperature"
        },
        "gemini": {
            "max_output_tokens": "max_output_tokens",
            "temperature": "temperature"
        }
    }
    
    @classmethod
    async def test_connectivity(cls, vendor: str, api_base: str, api_key: str) -> bool:
        """测试模型连通性"""
        try:
            config = cls.VENDOR_CONFIGS.get(vendor, {})
            headers = cls._build_headers(vendor, api_key, config)
            
            # 构建测试请求
            test_request = cls._build_test_request(vendor)
            url = f"{api_base}{config.get('api_path', '/v1/chat/completions')}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=test_request, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            print(f"连通性测试失败: {e}")
            return False
    
    @classmethod
    async def sync_request(
        cls,
        vendor: str,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步请求转发"""
        config = cls.VENDOR_CONFIGS.get(vendor, {})
        headers = cls._build_headers(vendor, api_key, config)
        
        # 参数映射
        mapped_request = cls._map_params(vendor, request_data)
        
        url = f"{api_base}{config.get('api_path', '/v1/chat/completions')}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=mapped_request, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            # 响应标准化为OpenAI格式
            return cls._standardize_response(vendor, response_data)
    
    @classmethod
    async def stream_request(
        cls,
        vendor: str,
        api_base: str,
        api_key: str,
        request_data: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式请求转发"""
        config = cls.VENDOR_CONFIGS.get(vendor, {})
        headers = cls._build_headers(vendor, api_key, config)
        
        # 参数映射
        mapped_request = cls._map_params(vendor, request_data)
        
        url = f"{api_base}{config.get('api_path', '/v1/chat/completions')}"
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, json=mapped_request, headers=headers) as response:
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
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
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
    def _build_test_request(cls, vendor: str) -> Dict:
        """构建测试请求"""
        if vendor == "claude":
            return {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]
            }
        else:
            return {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }
    
    @classmethod
    def _map_params(cls, vendor: str, request_data: Dict) -> Dict:
        """参数映射 - 将OpenAI参数转换为目标厂商格式"""
        mapping = cls.PARAM_MAPPING.get(vendor, {})
        mapped = request_data.copy()
        
        for openai_param, vendor_param in mapping.items():
            if openai_param in mapped and openai_param != vendor_param:
                mapped[vendor_param] = mapped.pop(openai_param)
        
        return mapped
    
    @classmethod
    def _standardize_response(cls, vendor: str, response_data: Dict) -> Dict:
        """响应标准化 - 将厂商响应转换为OpenAI格式"""
        standardized = {
            "id": response_data.get("id", f"chatcmpl-{id(response_data)}"),
            "object": "chat.completion",
            "created": response_data.get("created", 0),
            "model": response_data.get("model", "unknown"),
            "choices": [],
            "usage": {}
        }
        
        # 处理choices
        if "choices" in response_data:
            for choice in response_data["choices"]:
                standardized["choices"].append({
                    "index": choice.get("index", 0),
                    "message": {
                        "role": choice.get("message", {}).get("role", "assistant"),
                        "content": choice.get("message", {}).get("content", "")
                    },
                    "finish_reason": choice.get("finish_reason", "stop")
                })
        
        # 处理usage
        if "usage" in response_data:
            usage = response_data["usage"]
            standardized["usage"] = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        
        return standardized
    
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
                "choices": data_obj.get("choices", [])
            }
            
            return f"data: {json.dumps(standardized)}\n\n"
            
        except json.JSONDecodeError:
            return None
