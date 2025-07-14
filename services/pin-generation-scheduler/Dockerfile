# syntax=docker/dockerfile:1

FROM python:3.12-slim
WORKDIR /services/pin-generation-scheduler
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["python", "src/pin_generation_scheduler/main.py"]