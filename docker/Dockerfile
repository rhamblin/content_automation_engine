FROM python:3.13.5-slim

WORKDIR /app

# Entrypoint
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Shared code
COPY common ./common
ENV PYTHONPATH=/app

# --------
# Platform deps (cached across all services)
# --------
COPY requirements.platform.txt ./requirements.platform.txt
RUN pip install --no-cache-dir -r requirements.platform.txt

# --------
# Service deps + code
# --------
ARG SERVICE_NAME
ARG SERVICE_CMD

COPY services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/${SERVICE_NAME}/app/ ./app

CMD ${SERVICE_CMD}
