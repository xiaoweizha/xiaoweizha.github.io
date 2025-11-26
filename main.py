#!/usr/bin/env python3
"""
企业级RAG知识库系统 - 应用入口

生产环境启动入口文件。
"""

import uvicorn
from src.api.main import app
from src.utils.config import get_config

def main():
    """主函数"""
    config = get_config()

    print("🚀 启动企业级RAG知识库系统")
    print("=" * 50)
    print(f"环境: {config.server.environment}")
    print(f"版本: {config.system_version}")
    print(f"服务地址: http://{config.server.host}:{config.server.port}")
    print(f"API文档: http://{config.server.host}:{config.server.port}/docs")
    print("=" * 50)

    # 启动服务
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        workers=1,  # 在生产环境中应该使用gunicorn等WSGI服务器
        log_level=config.monitoring.log_level.lower(),
        access_log=True,
        reload=False  # 生产环境关闭自动重载
    )

if __name__ == "__main__":
    main()