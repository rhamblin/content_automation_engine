FROM python:3.13.5-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/content-generation-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/content-generation-worker/app/ ./app
CMD ["python", "-m", "app.content_generation_worker.app"]
