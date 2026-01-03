FROM python:3.12-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/post-generation-scheduler/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/post-generation-scheduler/app/ ./app/
CMD ["python", "app/post_generation_scheduler/scheduler.py"]