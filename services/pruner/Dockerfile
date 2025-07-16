FROM python:3.13.5-slim
WORKDIR /app
COPY common/db_core ./db_core
COPY services/pruner/main.py ./main.py
ENV PYTHONPATH=/app
CMD ["python", "main.py"]
