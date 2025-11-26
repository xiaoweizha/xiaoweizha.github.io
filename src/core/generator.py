"""
响应生成器模块

基于LLM生成智能回答。
"""

import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
import structlog

from .llm_providers import get_llm_provider, BaseLLMProvider
from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    """生成结果"""
    answer: str
    confidence: float
    tokens_used: int
    response_time: float
    model: str
    stop_reason: Optional[str] = None


class ResponseGenerator:
    """
    响应生成器

    基于检索到的上下文生成智能回答。
    """

    def __init__(self):
        self.config = get_config()
        self.llm_provider: Optional[BaseLLMProvider] = None

    async def initialize(self) -> None:
        """初始化生成器"""
        try:
            self.llm_provider = get_llm_provider()
            logger.info(
                "响应生成器初始化完成",
                provider=self.config.llm.provider,
                model=self.config.llm.model
            )
        except Exception as e:
            logger.error("响应生成器初始化失败", error=str(e))
            raise

    async def generate_response(
        self,
        query: str,
        context: str,
        language: str = "zh-CN",
        **kwargs
    ) -> GenerationResult:
        """
        生成回答

        Args:
            query: 用户查询
            context: 检索到的上下文
            language: 响应语言
            **kwargs: 其他参数

        Returns:
            生成结果
        """
        if not self.llm_provider:
            raise RuntimeError("响应生成器未初始化")

        start_time = time.time()

        try:
            # 构建提示词
            messages = self._build_messages(query, context, language)

            # 生成回答
            response = await self.llm_provider.generate(messages, **kwargs)

            # 计算置信度（简单实现）
            confidence = self._calculate_confidence(response, context)

            response_time = time.time() - start_time

            result = GenerationResult(
                answer=response["content"],
                confidence=confidence,
                tokens_used=response.get("tokens_used", 0),
                response_time=response_time,
                model=response.get("model", self.config.llm.model),
                stop_reason=response.get("stop_reason")
            )

            logger.info(
                "回答生成完成",
                query=query[:50],
                answer_length=len(result.answer),
                tokens_used=result.tokens_used,
                response_time=response_time,
                confidence=confidence
            )

            return result

        except Exception as e:
            logger.error("回答生成失败", query=query[:50], error=str(e))
            raise

    async def stream_generate_response(
        self,
        query: str,
        context: str,
        language: str = "zh-CN",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成回答

        Args:
            query: 用户查询
            context: 检索到的上下文
            language: 响应语言
            **kwargs: 其他参数

        Yields:
            生成的文本块
        """
        if not self.llm_provider:
            raise RuntimeError("响应生成器未初始化")

        start_time = time.time()
        accumulated_content = ""
        tokens_used = 0

        try:
            # 构建提示词
            messages = self._build_messages(query, context, language)

            # 流式生成
            async for chunk in self.llm_provider.stream_generate(messages, **kwargs):
                if chunk["type"] == "content":
                    accumulated_content += chunk["content"]
                    yield {
                        "type": "content",
                        "content": chunk["content"],
                        "accumulated_content": accumulated_content,
                        "model": chunk.get("model")
                    }
                elif chunk["type"] == "stop":
                    response_time = time.time() - start_time
                    confidence = self._calculate_confidence(
                        {"content": accumulated_content}, context
                    )

                    yield {
                        "type": "complete",
                        "content": "",
                        "final_answer": accumulated_content,
                        "confidence": confidence,
                        "tokens_used": tokens_used,
                        "response_time": response_time,
                        "model": chunk.get("model"),
                        "stop_reason": chunk.get("stop_reason")
                    }
                elif chunk["type"] == "error":
                    yield chunk

        except Exception as e:
            logger.error("流式生成失败", error=str(e))
            yield {
                "type": "error",
                "content": f"生成失败: {str(e)}"
            }

    def _build_messages(
        self,
        query: str,
        context: str,
        language: str
    ) -> List[Dict[str, str]]:
        """
        构建提示词消息

        Args:
            query: 用户查询
            context: 上下文
            language: 语言

        Returns:
            消息列表
        """
        # 根据语言选择系统提示
        if language == "zh-CN":
            system_prompt = """你是一个专业的知识库助手，基于提供的上下文回答用户问题。

规则：
1. 仅基于提供的上下文信息回答问题
2. 如果上下文中没有相关信息，明确说明"根据现有信息无法回答此问题"
3. 回答要准确、简洁、有条理
4. 可以适当引用上下文中的具体内容
5. 保持友好和专业的语气
6. 如果需要，可以提供相关的背景信息

上下文信息：
{context}

请基于以上信息回答用户的问题。"""
        else:
            system_prompt = """You are a professional knowledge base assistant. Answer user questions based on the provided context.

Rules:
1. Answer questions based only on the provided context information
2. If there's no relevant information in the context, clearly state "I cannot answer this question based on the available information"
3. Answers should be accurate, concise, and well-organized
4. You may appropriately cite specific content from the context
5. Maintain a friendly and professional tone
6. Provide relevant background information when necessary

Context Information:
{context}

Please answer the user's question based on the above information."""

        messages = [
            {
                "role": "system",
                "content": system_prompt.format(context=context)
            },
            {
                "role": "user",
                "content": query
            }
        ]

        return messages

    def _calculate_confidence(
        self,
        response: Dict[str, Any],
        context: str
    ) -> float:
        """
        计算回答置信度

        Args:
            response: LLM响应
            context: 上下文

        Returns:
            置信度 (0.0-1.0)
        """
        try:
            answer = response.get("content", "")

            # 简单的置信度计算
            confidence = 0.5  # 基础置信度

            # 如果回答包含"不知道"、"无法回答"等，降低置信度
            uncertain_phrases = [
                "不知道", "不清楚", "无法回答", "没有信息", "不确定",
                "don't know", "not sure", "cannot answer", "no information"
            ]

            for phrase in uncertain_phrases:
                if phrase in answer.lower():
                    confidence *= 0.3
                    break

            # 如果回答很短，可能信息不足
            if len(answer) < 50:
                confidence *= 0.8

            # 如果上下文很短，可能检索质量不高
            if len(context) < 100:
                confidence *= 0.7

            # 如果回答引用了具体信息，提高置信度
            if any(word in answer for word in ["根据", "显示", "表明", "according", "shows", "indicates"]):
                confidence = min(1.0, confidence * 1.2)

            return round(confidence, 2)

        except Exception as e:
            logger.warning("计算置信度失败", error=str(e))
            return 0.5

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            if not self.llm_provider:
                return {
                    "status": "unhealthy",
                    "error": "LLM提供商未初始化"
                }

            # 健康检查生成
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]

            start_time = time.time()
            response = await self.llm_provider.generate(test_messages, max_tokens=10)
            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "provider": self.config.llm.provider,
                "model": self.config.llm.model,
                "test_response_time": response_time,
                "test_tokens_used": response.get("tokens_used", 0)
            }

        except Exception as e:
            logger.error("响应生成器健康检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self) -> None:
        """
        关闭生成器，清理资源
        """
        # 这里可以添加资源清理逻辑
        logger.info("响应生成器已关闭")