FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI for testcontainers to work with mounted socket
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install test dependencies
COPY test/requirements.txt /app/test/requirements.txt
RUN pip install --no-cache-dir -r test/requirements.txt

# Copy common modules (your db_core, providers, etc.)
COPY common/ /app/common/

# Copy test files
COPY test/ /app/test/

# Set Python path so imports work
ENV PYTHONPATH=/app

# Run pytest by default
CMD ["pytest", "test/", "-v"]
