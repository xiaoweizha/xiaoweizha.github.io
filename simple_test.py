#!/usr/bin/env python3
import os
import anthropic

# 测试同步API调用
api_key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API Key: {api_key[:20]}...")

client = anthropic.Anthropic(api_key=api_key)

try:
    print("发送请求...")
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=20,
        messages=[{"role": "user", "content": "回复'测试成功'"}]
    )

    print(f"✅ 回复: {message.content[0].text}")
    print("🎉 Claude API正常工作！")

except Exception as e:
    print(f"❌ 错误: {e}")