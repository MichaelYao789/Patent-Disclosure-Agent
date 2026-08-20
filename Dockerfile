FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（Graphviz 用于流程图渲染）
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

CMD ["python", "-m", "patent_agent.main", "--input", "examples/input_brief.json"]
