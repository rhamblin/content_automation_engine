# syntax=docker/dockerfile:1

FROM python:3.13.5-slim
WORKDIR ./services/post-dispatcher
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["fastapi", "run", "src/post_dispatcher/dispatcher.py", "--port", "80"]
