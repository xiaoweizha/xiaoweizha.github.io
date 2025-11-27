#!/usr/bin/env python3
import asyncio
import os
import anthropic

async def test_real_anthropic():
    """测试真正的官方Anthropic API"""
    print("🌐 测试官方Anthropic API (api.anthropic.com)")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    print(f"API Key: {api_key[:20]}...")

    try:
        # 强制使用官方API，忽略任何BASE_URL设置
        client = anthropic.AsyncAnthropic(
            api_key=api_key
            # 不设置base_url，使用默认的官方API
        )

        print("📤 发送测试请求...")
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "请简单回复'Claude正常工作'"}]
        )

        content = response.content[0].text
        print(f"✅ Claude回复: {content}")
        print(f"📊 Token使用: {response.usage.input_tokens + response.usage.output_tokens}")
        return True

    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_real_anthropic())