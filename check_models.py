#!/usr/bin/env python3
import asyncio
import os
import httpx

async def check_available_models():
    """检查路由服务器支持的模型"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://ai-router.anker-in.com/bedrock")

    print(f"🔍 检查 {base_url} 支持的模型...")
    print(f"API Key: {api_key[:20]}...")

    async with httpx.AsyncClient() as client:
        try:
            # 测试1: 使用x-api-key头
            print("\n📋 方法1: x-api-key头")
            response = await client.get(
                f"{base_url}/v1/models",
                headers={"x-api-key": api_key}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                models = response.json()
                print("✅ 支持的模型:")
                for model in models.get('data', []):
                    print(f"  - {model.get('id', 'unknown')}")
            else:
                print(f"❌ 错误: {response.text}")

        except Exception as e:
            print(f"❌ x-api-key方法失败: {e}")

        try:
            # 测试2: 使用Authorization头
            print("\n📋 方法2: Authorization头")
            response = await client.get(
                f"{base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                models = response.json()
                print("✅ 支持的模型:")
                for model in models.get('data', []):
                    print(f"  - {model.get('id', 'unknown')}")
            else:
                print(f"❌ 错误: {response.text}")

        except Exception as e:
            print(f"❌ Authorization方法失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_available_models())