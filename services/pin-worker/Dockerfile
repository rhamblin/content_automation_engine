# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR /services/pin-worker
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["python", "src/pin_worker/worker.py"]