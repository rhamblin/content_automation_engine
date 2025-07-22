# syntax=docker/dockerfile:1

FROM python:3.12-slim
WORKDIR /services/pin-generation-scheduler
COPY common/constants ./common/constants
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["python", "app/pin_generation_scheduler/scheduler.py"]