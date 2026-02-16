FROM python:3.12-bookworm

WORKDIR /app

# Platform - install common package
COPY common ./common
RUN pip install --no-cache-dir -e ./common

# Seed worker deps
COPY db/seed-worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Seed worker code + tenant config
COPY db/seed-worker/seed.py ./seed.py
COPY config/tenants ./config/tenants

CMD ["python", "seed.py", "config/tenants"]
