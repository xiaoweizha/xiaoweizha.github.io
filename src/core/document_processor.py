"""
文档处理模块

支持多种格式文档的解析、分块、预处理等功能。
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib
import mimetypes

import structlog
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader
)

from ..models.schemas import Document, DocumentChunk
from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessorConfig:
    """文档处理器配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_doc: int = 1000
    supported_formats: List[str] = None
    enable_ocr: bool = False
    ocr_languages: List[str] = None

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [
                ".pdf", ".docx", ".doc", ".txt", ".md", ".html",
                ".pptx", ".ppt", ".xlsx", ".xls", ".csv"
            ]
        if self.ocr_languages is None:
            self.ocr_languages = ["chi_sim", "eng"]


class DocumentProcessor:
    """
    文档处理器

    支持多种格式文档的解析、分块和预处理。
    """

    def __init__(self, config: Optional[ProcessorConfig] = None):
        """
        初始化文档处理器

        Args:
            config: 处理器配置
        """
        self.config = config or ProcessorConfig()
        self.system_config = get_config()

        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""]
        )

        # 文档加载器映射
        self.loaders_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".doc": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".html": UnstructuredHTMLLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".ppt": UnstructuredPowerPointLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".xls": UnstructuredExcelLoader,
        }

        logger.info("文档处理器初始化完成", config=self.config)

    async def initialize(self) -> None:
        """异步初始化"""
        # 这里可以初始化OCR引擎、GPU资源等
        logger.info("文档处理器异步初始化完成")

    async def process_document(
        self,
        document: Document,
        extract_metadata: bool = True
    ) -> List[DocumentChunk]:
        """
        处理文档

        Args:
            document: 文档对象
            extract_metadata: 是否提取元数据

        Returns:
            文档块列表
        """
        try:
            logger.info(
                "开始处理文档",
                doc_id=document.id,
                filename=document.filename,
                file_size=len(document.content) if document.content else 0
            )

            # 1. 检查文件格式支持
            file_ext = Path(document.filename).suffix.lower()
            if file_ext not in self.config.supported_formats:
                raise ValueError(f"不支持的文件格式: {file_ext}")

            # 2. 解析文档内容
            text_content = await self._extract_text(document)

            # 3. 文档预处理
            processed_text = self._preprocess_text(text_content)

            # 4. 文档分块
            chunks = self._split_text(processed_text)

            # 5. 创建文档块对象
            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    id=f"{document.id}_chunk_{i}",
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i,
                    metadata={
                        "filename": document.filename,
                        "file_type": file_ext,
                        "chunk_size": len(chunk_text),
                        "document_title": document.metadata.get("title", ""),
                        "document_author": document.metadata.get("author", ""),
                        **document.metadata
                    }
                )

                # 提取块级元数据
                if extract_metadata:
                    chunk.metadata.update(
                        await self._extract_chunk_metadata(chunk_text)
                    )

                document_chunks.append(chunk)

            # 限制块数量
            if len(document_chunks) > self.config.max_chunks_per_doc:
                logger.warning(
                    "文档块数量超过限制，将截断",
                    doc_id=document.id,
                    chunks_count=len(document_chunks),
                    max_chunks=self.config.max_chunks_per_doc
                )
                document_chunks = document_chunks[:self.config.max_chunks_per_doc]

            logger.info(
                "文档处理完成",
                doc_id=document.id,
                chunks_count=len(document_chunks)
            )

            return document_chunks

        except Exception as e:
            logger.error(
                "文档处理失败",
                doc_id=document.id,
                filename=document.filename,
                error=str(e)
            )
            raise

    async def process_batch(
        self,
        documents: List[Document],
        max_concurrent: int = 5
    ) -> Dict[str, List[DocumentChunk]]:
        """
        批量处理文档

        Args:
            documents: 文档列表
            max_concurrent: 最大并发数

        Returns:
            文档ID到块列表的映射
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(doc: Document) -> tuple[str, List[DocumentChunk]]:
            async with semaphore:
                chunks = await self.process_document(doc)
                return doc.id, chunks

        tasks = [process_single(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        processed_docs = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("批量处理中文档处理失败", error=str(result))
                continue
            doc_id, chunks = result
            processed_docs[doc_id] = chunks

        logger.info(
            "批量文档处理完成",
            total_docs=len(documents),
            successful_docs=len(processed_docs)
        )

        return processed_docs

    async def _extract_text(self, document: Document) -> str:
        """
        提取文档文本内容

        Args:
            document: 文档对象

        Returns:
            提取的文本内容
        """
        file_ext = Path(document.filename).suffix.lower()

        try:
            if document.content:
                # 如果已有内容，直接使用
                if isinstance(document.content, bytes):
                    # 保存临时文件进行处理
                    temp_file = f"/tmp/{document.id}{file_ext}"
                    with open(temp_file, "wb") as f:
                        f.write(document.content)

                    loader_class = self.loaders_map.get(file_ext)
                    if not loader_class:
                        raise ValueError(f"不支持的文件格式: {file_ext}")

                    loader = loader_class(temp_file)
                    docs = loader.load()

                    # 清理临时文件
                    Path(temp_file).unlink(missing_ok=True)

                    return "\n\n".join([doc.page_content for doc in docs])
                else:
                    # 文本内容
                    return str(document.content)

            elif document.file_path:
                # 从文件路径加载
                loader_class = self.loaders_map.get(file_ext)
                if not loader_class:
                    raise ValueError(f"不支持的文件格式: {file_ext}")

                loader = loader_class(document.file_path)
                docs = loader.load()
                return "\n\n".join([doc.page_content for doc in docs])

            else:
                raise ValueError("文档内容和文件路径都为空")

        except Exception as e:
            logger.error(
                "文本提取失败",
                doc_id=document.id,
                file_type=file_ext,
                error=str(e)
            )

            # 如果是OCR可处理的图像格式，尝试OCR
            if self.config.enable_ocr and file_ext in [".png", ".jpg", ".jpeg", ".tiff"]:
                return await self._extract_text_with_ocr(document)

            raise

    async def _extract_text_with_ocr(self, document: Document) -> str:
        """
        使用OCR提取文本

        Args:
            document: 文档对象

        Returns:
            提取的文本内容
        """
        try:
            import pytesseract
            from PIL import Image
            import io

            # 处理图像
            if document.content:
                image = Image.open(io.BytesIO(document.content))
            else:
                image = Image.open(document.file_path)

            # OCR识别
            text = pytesseract.image_to_string(
                image,
                lang="+".join(self.config.ocr_languages)
            )

            logger.info(
                "OCR文本提取完成",
                doc_id=document.id,
                text_length=len(text)
            )

            return text

        except ImportError:
            logger.error("OCR功能需要安装pytesseract和pillow")
            raise
        except Exception as e:
            logger.error("OCR文本提取失败", doc_id=document.id, error=str(e))
            raise

    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理

        Args:
            text: 原始文本

        Returns:
            预处理后的文本
        """
        # 基础清理
        text = text.strip()

        # 移除过多的空白字符
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个连续换行符合并
        text = re.sub(r' {2,}', ' ', text)      # 多个连续空格合并
        text = re.sub(r'\t+', ' ', text)        # 制表符转空格

        # 移除特殊字符（保留中文、英文、数字、基本标点）
        text = re.sub(r'[^\u4e00-\u9fff\u0000-\u007f\s\.,;:!?()（）【】""''《》，。；：！？]', '', text)

        # 移除过短的行（可能是页眉页脚等）
        lines = text.split('\n')
        filtered_lines = [line for line in lines if len(line.strip()) > 10 or line.strip() == '']
        text = '\n'.join(filtered_lines)

        return text

    def _split_text(self, text: str) -> List[str]:
        """
        文本分块

        Args:
            text: 待分割的文本

        Returns:
            文本块列表
        """
        # 使用RecursiveCharacterTextSplitter进行分割
        chunks = self.text_splitter.split_text(text)

        # 过滤过短的块
        min_chunk_length = 50
        filtered_chunks = [
            chunk for chunk in chunks
            if len(chunk.strip()) >= min_chunk_length
        ]

        logger.debug(
            "文本分块完成",
            total_chunks=len(chunks),
            filtered_chunks=len(filtered_chunks)
        )

        return filtered_chunks

    async def _extract_chunk_metadata(self, chunk_text: str) -> Dict[str, Any]:
        """
        提取块级元数据

        Args:
            chunk_text: 文本块内容

        Returns:
            元数据字典
        """
        metadata = {}

        try:
            # 统计信息
            metadata.update({
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "sentence_count": len([s for s in chunk_text.split('。') if s.strip()]),
                "paragraph_count": len([p for p in chunk_text.split('\n\n') if p.strip()])
            })

            # 内容类型推断
            metadata["content_type"] = self._infer_content_type(chunk_text)

            # 语言检测（简单实现）
            metadata["language"] = self._detect_language(chunk_text)

            # 哈希值（用于去重）
            metadata["content_hash"] = hashlib.md5(chunk_text.encode()).hexdigest()

        except Exception as e:
            logger.warning("提取块级元数据失败", error=str(e))

        return metadata

    def _infer_content_type(self, text: str) -> str:
        """
        推断内容类型

        Args:
            text: 文本内容

        Returns:
            内容类型
        """
        text_lower = text.lower()

        # 简单的启发式规则
        if any(keyword in text_lower for keyword in ["图", "表", "fig", "table"]):
            return "figure_or_table"
        elif any(keyword in text_lower for keyword in ["摘要", "abstract", "总结", "summary"]):
            return "summary"
        elif any(keyword in text_lower for keyword in ["结论", "conclusion", "总结"]):
            return "conclusion"
        elif any(keyword in text_lower for keyword in ["介绍", "introduction", "概述"]):
            return "introduction"
        elif len([s for s in text.split('。') if '?' in s or '？' in s]) > 0:
            return "qa_or_discussion"
        else:
            return "general_content"

    def _detect_language(self, text: str) -> str:
        """
        检测语言

        Args:
            text: 文本内容

        Returns:
            语言代码
        """
        # 简单的中英文检测
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])

        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.5:
            return "zh-cn"
        elif chinese_ratio > 0.1:
            return "mixed"
        else:
            return "en"

    async def validate_document(self, document: Document) -> Dict[str, Any]:
        """
        验证文档

        Args:
            document: 文档对象

        Returns:
            验证结果
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {}
        }

        try:
            # 检查文件格式
            file_ext = Path(document.filename).suffix.lower()
            if file_ext not in self.config.supported_formats:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"不支持的文件格式: {file_ext}")

            # 检查文件大小
            if document.content:
                file_size = len(document.content)
                validation_result["metadata"]["file_size"] = file_size

                # 警告大文件
                if file_size > 50 * 1024 * 1024:  # 50MB
                    validation_result["warnings"].append("文件过大，处理可能较慢")

            # 尝试提取文本进行验证
            if validation_result["is_valid"]:
                try:
                    text_content = await self._extract_text(document)
                    validation_result["metadata"]["text_length"] = len(text_content)
                    validation_result["metadata"]["estimated_chunks"] = len(text_content) // self.config.chunk_size + 1

                    # 检查文本是否为空
                    if len(text_content.strip()) < 10:
                        validation_result["warnings"].append("文档内容过短")

                except Exception as e:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"文档解析失败: {str(e)}")

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"文档验证失败: {str(e)}")

        return validation_result

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            # 检查文本分割器
            sample_text = "健康检查文本样本，验证文档处理器功能正常。"
            chunks = self.text_splitter.split_text(sample_text)

            return {
                "status": "healthy",
                "text_splitter": "working",
                "supported_formats": len(self.config.supported_formats),
                "test_chunks": len(chunks)
            }

        except Exception as e:
            logger.error("文档处理器健康检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self) -> None:
        """
        关闭文档处理器，清理资源
        """
        # 这里可以清理临时文件、释放OCR引擎等
        logger.info("文档处理器已关闭")