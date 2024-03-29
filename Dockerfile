#拉取 python3.10 的基础镜像
FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip --no-cache && \
    pip install --no-cache -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]
