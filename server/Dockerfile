# 多阶段构建：构建阶段
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖（减少镜像体积）
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 运行阶段（极简镜像）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制虚拟环境和代码
COPY --from=builder /opt/venv /opt/venv
COPY server.py .
RUN mkdir -p server_data

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV ADMIN_PASSWORD=admin123
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"

# 启动命令
CMD ["python", "server.py"]
