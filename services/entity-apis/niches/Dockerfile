# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR /app
COPY common/db_core ./db_core
COPY common/constants ./common/constants
ENV PYTHONPATH=/app
COPY services/entity-apis/niches/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY services/entity-apis/niches/app/ ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]