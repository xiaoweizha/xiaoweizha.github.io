"""
WebSocket路由

实时通信和流式响应相关接口。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List
import json
import asyncio
import time

from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """建立连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket连接建立", client_id=client_id)

    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("WebSocket连接断开", client_id=client_id)

    async def send_personal_message(self, message: str, client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        """广播消息"""
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """WebSocket聊天接口"""
    await manager.connect(websocket, client_id)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 处理不同类型的消息
            message_type = message_data.get("type", "chat")

            if message_type == "chat":
                await handle_chat_message(websocket, client_id, message_data)
            elif message_type == "ping":
                await handle_ping(websocket, client_id)
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "未知的消息类型"
                }))

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error("WebSocket处理错误", client_id=client_id, error=str(e))
        manager.disconnect(client_id)


async def handle_chat_message(websocket: WebSocket, client_id: str, message_data: dict):
    """处理聊天消息"""
    try:
        query = message_data.get("message", "")

        if not query.strip():
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "消息不能为空"
            }))
            return

        # 发送处理中状态
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "正在思考中...",
            "timestamp": time.time()
        }))

        # TODO: 调用RAG引擎进行流式处理
        # 这里模拟流式响应
        response_text = f"这是对问题「{query}」的回答。RAG系统正在处理您的请求..."

        # 模拟流式输出
        words = response_text.split()
        accumulated_text = ""

        for i, word in enumerate(words):
            accumulated_text += word + " "

            # 发送部分响应
            await websocket.send_text(json.dumps({
                "type": "partial_response",
                "content": accumulated_text,
                "is_complete": False,
                "timestamp": time.time()
            }))

            # 模拟处理延迟
            await asyncio.sleep(0.1)

        # 发送完整响应
        await websocket.send_text(json.dumps({
            "type": "complete_response",
            "content": accumulated_text.strip(),
            "sources": [
                {"title": "知识库文档1", "score": 0.95},
                {"title": "知识库文档2", "score": 0.87}
            ],
            "confidence": 0.92,
            "is_complete": True,
            "timestamp": time.time()
        }))

    except Exception as e:
        logger.error("处理聊天消息失败", client_id=client_id, error=str(e))
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "处理消息时出错"
        }))


async def handle_ping(websocket: WebSocket, client_id: str):
    """处理心跳消息"""
    await websocket.send_text(json.dumps({
        "type": "pong",
        "timestamp": time.time()
    }))


@router.websocket("/system/monitor/{client_id}")
async def websocket_monitor(websocket: WebSocket, client_id: str):
    """WebSocket系统监控接口"""
    await manager.connect(websocket, client_id)

    try:
        while True:
            # 发送系统监控数据
            monitor_data = {
                "type": "system_stats",
                "data": {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "active_sessions": len(manager.active_connections),
                    "timestamp": time.time()
                }
            }

            await websocket.send_text(json.dumps(monitor_data))

            # 等待5秒后发送下一次数据
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error("WebSocket监控错误", client_id=client_id, error=str(e))
        manager.disconnect(client_id)


@router.get("/connections")
async def get_active_connections():
    """获取活跃连接数"""
    return {
        "active_connections": len(manager.active_connections),
        "connection_ids": list(manager.active_connections.keys())
    }