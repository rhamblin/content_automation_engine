FROM python:3.13.5-slim
WORKDIR /app
COPY common/db_core ./db_core
ENV PYTHONPATH=/app
COPY services/projects-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/projects-api/app/ ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
