FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制并安装根目录的依赖（包含 Scrapy）
COPY requirements.txt /tmp/root_requirements.txt
RUN pip install --no-cache-dir -r /tmp/root_requirements.txt

# 复制并安装后端依赖
COPY backend/requirements.txt /tmp/backend_requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend_requirements.txt

# 复制后端应用代码
COPY backend/ /app/

# 复制 Scrapy 项目（用于爬虫功能）
COPY scrapy_project/ /app/scrapy_project/

# 复制配置文件和工具模块
COPY config.json /app/config.json
COPY utils/ /app/utils/

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]
