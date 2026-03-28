#!/usr/bin/env python3
"""测试 Anthropic /v1/messages 接口的 tool_use 支持"""

import requests
import json

GATEWAY_URL = "http://localhost:8080"
API_KEY = "test-api-key-12345"

tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
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
print("Anthropic /v1/messages Tool Use 支持测试")
print("=" * 70)

for model_id, display_name in models_to_test:
    print(f"\n【测试】{display_name}")

    try:
        resp = requests.post(
            f'{GATEWAY_URL}/v1/messages',
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "北京天气怎么样"}],
                "tools": tools,
                "tool_choice": {"type": "function", "name": "get_weather"},
                "max_tokens": 500
            },
            timeout=60
        )

        if resp.status_code == 200:
            result = resp.json()
            content = result.get('content', [])

            # 查找 tool_use 块
            tool_uses = [c for c in content if isinstance(c, dict) and c.get('type') == 'tool_use']
            text_blocks = [c for c in content if isinstance(c, dict) and c.get('type') == 'text']

            if tool_uses:
                print(f"  ✅ 返回 tool_use:")
                for tu in tool_uses:
                    print(f"     - {tu.get('name', '')}: {json.dumps(tu.get('input', {}))}")
            elif text_blocks:
                print(f"  ⚠️  返回文本：{text_blocks[0].get('text', '')[:100]}...")
            else:
                print(f"  ❌ 未知响应格式：{content}")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:100]}")

    except Exception as e:
        print(f"  ❌ 错误：{e}")

print("\n" + "=" * 70)
