FROM python:3.11-slim

# 避免输出缓存，方便日志
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 统一工作目录（关键：import 从这里找）
WORKDIR /app

# 安装系统依赖（如果你有 mysqlclient / pdf / ocr 等依赖可在这里加）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖文件，利用 Docker cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 再拷贝业务代码
COPY . /app

# 保险：明确 Python 的搜索路径根
ENV PYTHONPATH=/app

# 如果你的后端会监听端口（例如 8000），可以开放（不影响 CLI）
EXPOSE 8000

# 按你当前的启动方式
CMD ["python", "-m", "inter_face"]
