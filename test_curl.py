#!/usr/bin/env python3
import os
import subprocess
import json

api_key = os.environ.get("ANTHROPIC_API_KEY")

# 构建curl命令
curl_cmd = [
    "curl", "-X", "POST",
    "https://api.anthropic.com/v1/messages",
    "-H", f"Authorization: Bearer {api_key}",
    "-H", "Content-Type: application/json",
    "-H", "anthropic-version: 2023-06-01",
    "-d", json.dumps({
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 20,
        "messages": [{"role": "user", "content": "回复'API正常'"}]
    }),
    "--connect-timeout", "10",
    "--max-time", "30"
]

print("🔬 使用curl直接测试官方API...")
try:
    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=35)
    print(f"状态码: {result.returncode}")
    print(f"响应: {result.stdout}")
    if result.stderr:
        print(f"错误: {result.stderr}")

    if result.returncode == 0 and "content" in result.stdout:
        print("✅ curl测试成功")
    else:
        print("❌ curl测试失败")

except subprocess.TimeoutExpired:
    print("❌ curl超时")
except Exception as e:
    print(f"❌ curl异常: {e}")