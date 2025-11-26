"""
智能问答路由

RAG问答和对话相关接口。
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import time

from ...utils.logger import get_logger
from ...models.schemas import QueryRequest, QueryResponse
from .auth import get_current_user, UserInfo

router = APIRouter()
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user, assistant, system
    content: str
    timestamp: float


class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str
    messages: List[ChatMessage]
    created_at: float


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    mode: str = "hybrid"
    top_k: int = 5


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: ChatRequest,
    http_request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """智能问答接口"""
    try:
        # 获取RAG引擎
        rag_engine = http_request.app.state.rag_engine

        # 构建查询请求
        query_request = QueryRequest(
            query=request.message,
            mode=request.mode,
            top_k=request.top_k
        )

        # 执行RAG查询
        result = await rag_engine.query(query_request)

        logger.info(
            "问答请求完成",
            user=current_user.username,
            query=request.message,
            mode=request.mode,
            confidence=result.confidence
        )

        return result

    except Exception as e:
        logger.error(
            "问答请求失败",
            user=current_user.username,
            query=request.message,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/sessions")
async def list_chat_sessions(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取聊天会话列表"""
    try:
        # TODO: 从数据库获取用户的聊天会话
        mock_sessions = [
            {
                "session_id": "session1",
                "title": "RAG技术咨询",
                "last_message": "什么是RAG技术？",
                "created_at": time.time() - 3600,
                "updated_at": time.time() - 1800
            }
        ]

        return {
            "sessions": mock_sessions,
            "total": len(mock_sessions)
        }

    except Exception as e:
        logger.error("获取聊天会话失败", user=current_user.username, error=str(e))
        raise HTTPException(status_code=500, detail="获取聊天会话失败")


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """获取聊天会话详情"""
    try:
        # TODO: 从数据库获取聊天会话详情
        if session_id == "session1":
            return ChatSession(
                session_id=session_id,
                messages=[
                    ChatMessage(
                        role="user",
                        content="什么是RAG技术？",
                        timestamp=time.time() - 3600
                    ),
                    ChatMessage(
                        role="assistant",
                        content="RAG（检索增强生成）是一种结合了信息检索和生成式AI的技术...",
                        timestamp=time.time() - 3590
                    )
                ],
                created_at=time.time() - 3600
            )
        else:
            raise HTTPException(status_code=404, detail="聊天会话不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取聊天会话详情失败", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取聊天会话详情失败")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """删除聊天会话"""
    try:
        # TODO: 实际的删除逻辑
        logger.info("聊天会话删除成功", session_id=session_id, user=current_user.username)
        return {"message": "聊天会话删除成功"}

    except Exception as e:
        logger.error("删除聊天会话失败", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="删除聊天会话失败")