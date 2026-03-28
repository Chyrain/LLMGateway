#!/usr/bin/env python3
"""测试各模型对 tool calls 的支持"""

import requests
import json

GATEWAY_URL = "http://localhost:8080"
API_KEY = "test-api-key-12345"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]

models_to_test = [
    ("qwen3.5-plus", "qwen3.5-plus (bailian)"),
    ("glm-5", "glm-5 (bailian)"),
    ("kimi-k2.5", "kimi-k2.5 (bailian)"),
    ("MiniMax-M2.5", "MiniMax-M2.5 (bailian)"),
]

print("=" * 70)
print("Tool Calls 支持测试 (tool_choice=auto)")
print("=" * 70)

for model_id, display_name in models_to_test:
    print(f"\n【测试】{display_name}")

    try:
        resp = requests.post(
            f'{GATEWAY_URL}/v1/chat/completions',
            headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "北京天气怎么样"}],
                "tools": tools,
                # 使用 auto 而不是 forced
                "tool_choice": "auto",
                "max_tokens": 500,
                "stream": False
            },
            timeout=60
        )

        if resp.status_code == 200:
            result = resp.json()
            choices = result.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '无')
                tool_calls = message.get('tool_calls', None)

                if tool_calls:
                    print(f"  ✅ 支持 tool_calls")
                    for tc in tool_calls:
                        func = tc.get('function', {})
                        print(f"     - 调用：{func.get('name', '')}({func.get('arguments', '{}')})")
                else:
                    print(f"  ⚠️  返回文本：{content[:100]}...")
            else:
                print(f"  ❌ 无响应")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:100]}")

    except Exception as e:
        print(f"  ❌ 错误：{e}")

print("\n" + "=" * 70)
