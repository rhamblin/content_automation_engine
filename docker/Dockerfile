FROM python:3.13.5-slim

WORKDIR /app

# Entrypoint
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Platform - install common package with all dependencies
COPY common ./common
RUN pip install --no-cache-dir -e ./common
ENV PYTHONPATH=/app

# --------
# Service deps + code
# --------
ARG SERVICE_NAME
ARG SERVICE_CMD

ENV SERVICE_NAME=${SERVICE_NAME}

COPY services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/${SERVICE_NAME}/app/ ./app

CMD sh -c "python -m app.$(echo $SERVICE_NAME | tr '-' '_').app"