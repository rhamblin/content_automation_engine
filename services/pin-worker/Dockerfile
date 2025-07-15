# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR /src
COPY common/db_core ./db_core
COPY services/pin-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/pin-worker/src/ ./src
CMD ["python", "src/pin_worker/worker.py"]