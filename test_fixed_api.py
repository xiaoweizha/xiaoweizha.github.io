#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('.')

from src.core.llm_providers import AnthropicProvider

async def test_fixed_api():
    """测试修改后的API调用"""
    config = {
        "model": "claude-3-5-sonnet-20241022",
        "api_key": os.environ.get("ANTHROPIC_API_KEY"),
        "api_base": None,
        "temperature": 0.1,
        "max_tokens": 100,
        "timeout": 60
    }

    provider = AnthropicProvider(config)

    messages = [{"role": "user", "content": "请回复'测试成功'"}]

    try:
        result = await provider.generate(messages)
        print(f"✅ Claude回复: {result['content']}")
        print(f"📊 Tokens: {result['tokens_used']}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_api())
    if success:
        print("🎉 修复成功！Claude API正常工作！")
    else:
        print("❌ 修复失败，需要进一步调试")