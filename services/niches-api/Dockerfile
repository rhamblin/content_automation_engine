# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR ./services/niches-api
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["fastapi", "run", "src/api/api.py", "--port", "80"]
