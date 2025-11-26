# 企业级RAG知识库系统 Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    libreoffice \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装Python依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev \
    && rm -rf $POETRY_CACHE_DIR

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs storage/documents storage/exports storage/temp

# 设置权限
RUN chmod +x scripts/*.py

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]