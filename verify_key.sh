#!/bin/bash

echo "🔑 验证 Anthropic API Key..."

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY 环境变量未设置"
    exit 1
fi

echo "📋 API Key: ${ANTHROPIC_API_KEY:0:10}...${ANTHROPIC_API_KEY: -6}"

echo "🌐 测试官方API连接..."
response=$(curl -s -w "\n%{http_code}" -X POST \
    "https://api.anthropic.com/v1/messages" \
    -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
    -H "Content-Type: application/json" \
    -H "anthropic-version: 2023-06-01" \
    -d '{
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "hi"}]
    }' \
    --connect-timeout 10 \
    --max-time 30)

# 分离响应内容和状态码
http_code=$(echo "$response" | tail -n1)
content=$(echo "$response" | head -n -1)

echo "HTTP状态码: $http_code"
echo "响应内容: $content"

if [ "$http_code" = "200" ]; then
    echo "✅ API Key 有效！Claude API正常工作"
elif [ "$http_code" = "401" ]; then
    echo "❌ API Key 无效或已过期"
    echo "   请到 https://console.anthropic.com 获取新的API key"
elif [ "$http_code" = "429" ]; then
    echo "⚠️  API Key 有效，但达到速率限制"
elif [ "$http_code" = "400" ]; then
    echo "⚠️  API Key 有效，但请求格式有问题"
else
    echo "❓ 未知状态: $http_code"
fi