FROM python:3.13.5-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/content-generation-dispatcher/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/content-generation-dispatcher/app/content_generation_dispatcher ./content_generation_dispatcher
CMD ["fastapi", "run", "content_generation_dispatcher/dispatcher.py", "--port", "80"]