FROM python:3.13.5-slim
WORKDIR /app
COPY common ./common
ENV PYTHONPATH=/app
COPY services/post-dispatcher/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/post-dispatcher/app/post_dispatcher ./post_dispatcher
CMD ["fastapi", "run", "post_dispatcher/dispatcher.py", "--port", "80"]