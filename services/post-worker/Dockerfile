-- Active: 1767067788563@@127.0.0.1@5432@contentengine_development
FROM python:3.13.5-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/post-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/post-worker/app/ ./app
CMD ["python", "-m", "app.post_worker.app"]
