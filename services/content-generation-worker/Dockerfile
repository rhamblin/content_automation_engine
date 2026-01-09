FROM python:3.13.5-slim

WORKDIR /app

# Entrypoint: normalize local secrets → env (no-op in cloud)
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Shared code
COPY common ./common
ENV PYTHONPATH=/app

# Service-specific (parameterized)
ARG SERVICE_NAME
ARG SERVICE_CMD

COPY services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/${SERVICE_NAME}/app/ ./app

CMD ${SERVICE_CMD}
