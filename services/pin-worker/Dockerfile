# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR /app
COPY common/db_core ./db_core
ENV PYTHONPATH=/app
COPY services/pin-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/pin-worker/app/ ./app
CMD ["python", "app/pin_worker/worker.py"]