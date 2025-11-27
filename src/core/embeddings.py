"""
嵌入向量生成模块

支持多种嵌入模型的统一接口。
"""

import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np
import structlog

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """嵌入提供商基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model")
        self.dimension = config.get("dimension", 1536)
        self.batch_size = config.get("batch_size", 100)

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本的嵌入向量"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI嵌入提供商"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=config.get("api_key"),
                base_url=config.get("api_base")
            )
            logger.info("OpenAI嵌入客户端初始化成功", model=self.model)
        except ImportError:
            logger.error("请安装openai包: pip install openai")
            raise
        except Exception as e:
            logger.error("OpenAI嵌入客户端初始化失败", error=str(e))
            raise

    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error("生成嵌入向量失败", error=str(e))
            # 返回随机向量作为回退
            return np.random.normal(0, 1, self.dimension).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本的嵌入向量"""
        try:
            # 分批处理
            all_embeddings = []

            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts
                )

                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

            return all_embeddings

        except Exception as e:
            logger.error("批量生成嵌入向量失败", error=str(e))
            # 返回随机向量作为回退
            return [np.random.normal(0, 1, self.dimension).tolist() for _ in texts]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """模拟嵌入提供商（用于测试）"""

    async def embed_text(self, text: str) -> List[float]:
        """生成模拟嵌入向量"""
        # 基于文本内容生成一致性的随机向量
        np.random.seed(hash(text) % 2**32)
        return np.random.normal(0, 1, self.dimension).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成模拟嵌入向量"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings


class EmbeddingProviderFactory:
    """嵌入提供商工厂"""

    _providers = {
        "openai": OpenAIEmbeddingProvider,
        "mock": MockEmbeddingProvider,
    }

    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> BaseEmbeddingProvider:
        """
        创建嵌入提供商实例

        Args:
            provider_type: 提供商类型
            config: 配置参数

        Returns:
            嵌入提供商实例
        """
        if provider_type not in cls._providers:
            raise ValueError(f"不支持的嵌入提供商: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供商列表"""
        return list(cls._providers.keys())


# 便捷函数
def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    获取配置的嵌入提供商实例

    Returns:
        嵌入提供商实例
    """
    config = get_config()

    # 如果没有OpenAI配置，使用模拟提供商
    if config.embedding.provider == "openai" and not hasattr(config.llm, 'openai_api_key'):
        provider_type = "mock"
        provider_config = {
            "model": config.embedding.model,
            "dimension": config.embedding.dimension,
            "batch_size": config.embedding.batch_size
        }
    else:
        provider_type = config.embedding.provider
        provider_config = {
            "model": config.embedding.model,
            "dimension": config.embedding.dimension,
            "batch_size": config.embedding.batch_size,
            "api_key": getattr(config.llm, 'openai_api_key', None),
            "api_base": getattr(config.llm, 'openai_api_base', None)
        }

    return EmbeddingProviderFactory.create_provider(provider_type, provider_config)