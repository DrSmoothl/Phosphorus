# Multi-stage Dockerfile for Phosphorus
FROM python:3.11-slim as builder

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY lib/ lib/

# 安装依赖
RUN uv sync --frozen

# 运行时阶段
FROM python:3.11-slim as runtime

# 安装Java (JPlag需要)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# 复制uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 创建非root用户
RUN useradd --create-home --shell /bin/bash phosphorus

# 设置工作目录
WORKDIR /app

# 复制应用文件
COPY --from=builder --chown=phosphorus:phosphorus /app ./

# 切换到非root用户
USER phosphorus

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PHOSPHORUS_HOST=0.0.0.0
ENV PHOSPHORUS_PORT=8000

# 启动命令
CMD ["uv", "run", "python", "-m", "src.main"]
