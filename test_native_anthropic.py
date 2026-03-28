#!/usr/bin/env python3
"""
测试原生 Anthropic 格式透传功能

验证当厂商支持 anthropic 格式时，请求能够原生透传而不进行转换
"""

import json
import requests

# 网关配置
GATEWAY_BASE = "http://localhost:8080"
GATEWAY_API_KEY = "test-api-key-12345"

HEADERS = {
    "Authorization": f"Bearer {GATEWAY_API_KEY}",
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
}


def test_anthropic_format(vendor: str, model: str, system: str = None):
    """测试 Anthropic 格式请求"""
    print(f"\n{'='*60}")
    print(f"测试：{vendor} - {model}")
    print(f"{'='*60}")

    # 构建 Anthropic 格式请求
    request_body = {
        "model": model,
        "messages": [
            {"role": "user", "content": "你好，请介绍一下自己"}
        ],
        "max_tokens": 1024,
        "stream": False,
    }

    if system:
        request_body["system"] = system

    try:
        response = requests.post(
            f"{GATEWAY_BASE}/v1/messages",
            headers=HEADERS,
            json=request_body,
            timeout=60,
        )

        print(f"状态码：{response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"响应 ID: {result.get('id', 'N/A')}")
            print(f"角色：{result.get('role', 'N/A')}")
            print(f"模型：{result.get('model', 'N/A')}")
            print(f"停止原因：{result.get('stop_reason', 'N/A')}")

            # 打印内容
            content = result.get("content", [])
            print(f"\n内容块数量：{len(content)}")
            for i, block in enumerate(content):
                if isinstance(block, dict):
                    block_type = block.get("type", "unknown")
                    if block_type == "text":
                        print(f"  [{i}] 类型：text")
                        print(f"      内容：{block.get('text', '')[:200]}...")
                    elif block_type == "tool_use":
                        print(f"  [{i}] 类型：tool_use")
                        print(f"      ID: {block.get('id', 'N/A')}")
                        print(f"      名称：{block.get('name', 'N/A')}")
                        print(f"      输入：{json.dumps(block.get('input', {}), ensure_ascii=False)}")
                else:
                    print(f"  [{i}] 未知格式：{block}")

            # 打印使用量
            usage = result.get("usage", {})
            if usage:
                print(f"\n使用量：")
                print(f"  输入 Token: {usage.get('input_tokens', 0)}")
                print(f"  输出 Token: {usage.get('output_tokens', 0)}")
                print(f"  总 Token: {usage.get('total_tokens', 0)}")

            return True
        else:
            print(f"错误：{response.text[:500]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求异常：{e}")
        return False


def test_tool_use(vendor: str, model: str):
    """测试 tool_use 功能"""
    print(f"\n{'='*60}")
    print(f"测试 Tool Use: {vendor} - {model}")
    print(f"{'='*60}")

    # 构建带 tool 的 Anthropic 格式请求
    request_body = {
        "model": model,
        "messages": [
            {"role": "user", "content": "请查询北京今天的天气"}
        ],
        "max_tokens": 1024,
        "tools": [
            {
                "name": "get_weather",
                "description": "获取指定城市的天气信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        }
                    },
                    "required": ["city"]
                }
            }
        ],
        "stream": False,
    }

    try:
        response = requests.post(
            f"{GATEWAY_BASE}/v1/messages",
            headers=HEADERS,
            json=request_body,
            timeout=60,
        )

        print(f"状态码：{response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result.get("content", [])

            # 检查是否有 tool_use
            has_tool_use = False
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    has_tool_use = True
                    print(f"\n发现 tool_use:")
                    print(f"  ID: {block.get('id', 'N/A')}")
                    print(f"  名称：{block.get('name', 'N/A')}")
                    print(f"  输入：{json.dumps(block.get('input', {}), ensure_ascii=False)}")

            if has_tool_use:
                print("\n✓ Tool Use 测试成功!")
            else:
                print("\n 未检测到 tool_use，可能是模型选择不支持")

            return has_tool_use
        else:
            print(f"错误：{response.text[:500]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求异常：{e}")
        return False


if __name__ == "__main__":
    print("原生 Anthropic 格式透传测试")
    print("=" * 60)

    # 测试支持原生 Anthropic 格式的厂商模型
    test_cases = [
        ("qwen", "qwen3.5-plus"),  # 阿里通义千问 - 支持 anthropic
        ("bailian", "MiniMax-M2.5"),  # 阿里百炼 - 支持 anthropic (MiniMax 模型)
        ("bailian", "glm-5"),  # 阿里百炼 - 支持 anthropic (智谱模型)
        ("minimax", "MiniMax-M2.7"),  # MiniMax - 支持 anthropic
    ]

    for vendor, model in test_cases:
        success = test_anthropic_format(vendor, model)
        if success:
            print(f"✓ {vendor} - {model} 测试通过")
        else:
            print(f"✗ {vendor} - {model} 测试失败")

    # 测试 tool_use - 使用 bailian 厂商的 MiniMax-M2.5 模型
    test_tool_use("bailian", "MiniMax-M2.5")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
