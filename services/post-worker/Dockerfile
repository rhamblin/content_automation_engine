FROM python:3.13.5-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/post-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/post-worker/app/ ./app
CMD ["python", "app/post_worker/worker.py"]
