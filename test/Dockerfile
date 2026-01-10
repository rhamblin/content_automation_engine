FROM python:3.11-slim

WORKDIR /app

# Install test dependencies
COPY test/requirements.txt /app/test/requirements.txt
RUN pip install --no-cache-dir -r test/requirements.txt

COPY common/ /app/common/

# Copy test files
COPY test/ /app/test/

# Set Python path so imports work
ENV PYTHONPATH=/app

# Run pytest by default
CMD ["pytest", "test/", "-v"]
