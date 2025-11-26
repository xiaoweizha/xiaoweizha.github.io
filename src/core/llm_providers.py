"""
LLM提供商集成模块

支持多种LLM提供商的统一接口。
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import structlog

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    """LLM提供商基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model")
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60)

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """生成回答"""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成回答"""
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.api_base
            )
            logger.info("Anthropic Claude客户端初始化成功", model=self.model)
        except ImportError:
            logger.error("请安装anthropic包: pip install anthropic")
            raise
        except Exception as e:
            logger.error("Anthropic Claude客户端初始化失败", error=str(e))
            raise

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成回答

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Returns:
            生成结果
        """
        try:
            # 转换消息格式
            claude_messages = self._convert_messages(messages)

            # 调用Claude API
            response = await self.client.messages.create(
                model=self.model,
                messages=claude_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )

            # 解析响应
            result = {
                "content": response.content[0].text if response.content else "",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": response.model,
                "stop_reason": response.stop_reason
            }

            logger.debug(
                "Claude生成完成",
                model=self.model,
                tokens_used=result["tokens_used"],
                content_length=len(result["content"])
            )

            return result

        except Exception as e:
            logger.error("Claude生成失败", error=str(e), model=self.model)
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成回答

        Args:
            messages: 对话消息列表
            **kwargs: 其他参数

        Yields:
            生成的文本块
        """
        try:
            # 转换消息格式
            claude_messages = self._convert_messages(messages)

            # 流式调用Claude API
            async with self.client.messages.stream(
                model=self.model,
                messages=claude_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        yield {
                            "type": "content",
                            "content": event.delta.text,
                            "model": self.model
                        }
                    elif event.type == "message_stop":
                        yield {
                            "type": "stop",
                            "content": "",
                            "model": self.model,
                            "stop_reason": "end_turn"
                        }

        except Exception as e:
            logger.error("Claude流式生成失败", error=str(e))
            yield {
                "type": "error",
                "content": f"生成失败: {str(e)}",
                "model": self.model
            }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        转换消息格式为Claude格式

        Args:
            messages: 通用消息格式

        Returns:
            Claude消息格式
        """
        claude_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            # Claude使用user和assistant角色
            if role == "system":
                # 系统消息作为第一条用户消息
                claude_messages.append({
                    "role": "user",
                    "content": f"System: {content}"
                })
            elif role == "user":
                claude_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                claude_messages.append({
                    "role": "assistant",
                    "content": content
                })

        return claude_messages


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            logger.info("OpenAI客户端初始化成功", model=self.model)
        except ImportError:
            logger.error("请安装openai包: pip install openai")
            raise
        except Exception as e:
            logger.error("OpenAI客户端初始化失败", error=str(e))
            raise

    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """生成回答"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )

            result = {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "model": response.model,
                "stop_reason": response.choices[0].finish_reason
            }

            return result

        except Exception as e:
            logger.error("OpenAI生成失败", error=str(e))
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成回答"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content,
                        "model": self.model
                    }

                if chunk.choices[0].finish_reason:
                    yield {
                        "type": "stop",
                        "content": "",
                        "model": self.model,
                        "stop_reason": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            logger.error("OpenAI流式生成失败", error=str(e))
            yield {
                "type": "error",
                "content": f"生成失败: {str(e)}",
                "model": self.model
            }


class LLMProviderFactory:
    """LLM提供商工厂"""

    _providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        # 可以继续添加其他提供商
    }

    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """
        创建LLM提供商实例

        Args:
            provider_type: 提供商类型
            config: 配置参数

        Returns:
            LLM提供商实例
        """
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的LLM提供商: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供商列表"""
        return list(cls._providers.keys())


# 便捷函数
def get_llm_provider() -> BaseLLMProvider:
    """
    获取配置的LLM提供商实例

    Returns:
        LLM提供商实例
    """
    config = get_config()

    provider_config = {
        "model": config.llm.model,
        "api_key": config.llm.openai_api_key if config.llm.provider == "openai" else getattr(config.llm, f"{config.llm.provider}_api_key", None),
        "api_base": getattr(config.llm, f"{config.llm.provider}_api_base", None) or config.llm.openai_api_base,
        "temperature": config.llm.temperature,
        "max_tokens": config.llm.max_tokens,
        "timeout": config.llm.timeout
    }

    return LLMProviderFactory.create_provider(config.llm.provider, provider_config)