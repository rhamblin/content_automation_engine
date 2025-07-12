# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /services/pin-generation-service
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY /src ./src
CMD ["python", "src/generate_pin.py"]