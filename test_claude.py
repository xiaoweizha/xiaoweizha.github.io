#!/usr/bin/env python3
import asyncio
import os
import anthropic

async def test_official_api():
    """测试官方Anthropic API"""
    print("=== 测试官方Anthropic API ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY 环境变量未设置")
        return False

    print(f"✅ API Key: {api_key[:20]}...")

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)

        print("📤 发送请求到官方API...")
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": "你好，请回复'官方API正常'"}]
        )

        content = response.content[0].text
        print(f"✅ 官方API响应: {content}")
        return True

    except Exception as e:
        print(f"❌ 官方API失败: {e}")
        return False

async def test_router_with_x_api_key():
    """测试路由服务器，使用x-api-key头"""
    print("\n=== 测试路由服务器 (x-api-key) ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    if not base_url:
        print("❌ ANTHROPIC_BASE_URL 环境变量未设置")
        return False

    print(f"✅ Base URL: {base_url}")
    print(f"✅ API Key: {api_key[:20]}...")

    try:
        import httpx

        # 创建自定义HTTP客户端，使用x-api-key头
        http_client = httpx.AsyncClient(
            headers={"x-api-key": api_key}
        )

        client = anthropic.AsyncAnthropic(
            api_key="placeholder",  # 占位符
            base_url=base_url,
            http_client=http_client
        )

        print("📤 发送请求到路由服务器...")
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": "你好，请回复'路由服务器正常'"}]
        )

        content = response.content[0].text
        print(f"✅ 路由服务器响应: {content}")
        return True

    except Exception as e:
        print(f"❌ 路由服务器失败: {e}")
        return False

async def test_router_with_auth_header():
    """测试路由服务器，使用Authorization头"""
    print("\n=== 测试路由服务器 (Authorization) ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")

    if not base_url:
        print("❌ ANTHROPIC_BASE_URL 环境变量未设置")
        return False

    try:
        client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=base_url
        )

        print("📤 发送请求到路由服务器...")
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": "你好，请回复'标准认证正常'"}]
        )

        content = response.content[0].text
        print(f"✅ 标准认证响应: {content}")
        return True

    except Exception as e:
        print(f"❌ 标准认证失败: {e}")
        return False

async def main():
    print("🔬 Claude API 连通性测试\n")

    # 测试1: 官方API
    official_ok = await test_official_api()

    # 测试2: 路由服务器 x-api-key
    router_x_ok = await test_router_with_x_api_key()

    # 测试3: 路由服务器 Authorization
    router_auth_ok = await test_router_with_auth_header()

    print(f"\n📊 测试结果:")
    print(f"官方API: {'✅' if official_ok else '❌'}")
    print(f"路由服务器 (x-api-key): {'✅' if router_x_ok else '❌'}")
    print(f"路由服务器 (Authorization): {'✅' if router_auth_ok else '❌'}")

    if official_ok:
        print("\n🎯 建议使用官方API")
    elif router_x_ok:
        print("\n🎯 建议使用路由服务器 + x-api-key头")
    elif router_auth_ok:
        print("\n🎯 建议使用路由服务器 + Authorization头")
    else:
        print("\n❌ 所有方法都失败了")

if __name__ == "__main__":
    asyncio.run(main())