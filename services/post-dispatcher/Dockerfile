# syntax=docker/dockerfile:1
FROM python:3.13.5-slim
WORKDIR /app
COPY common/constants ./common/constants
COPY services/post-dispatcher/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/post-dispatcher/app/ ./app
CMD ["uvicorn", "post_dispatcher.dispatcher:app", "--host", "0.0.0.0", "--port", "80"]
