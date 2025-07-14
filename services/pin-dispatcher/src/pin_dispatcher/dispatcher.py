from fastapi import FastAPI
from redis import Redis
import json
import uuid

app = FastAPI()
queue = Redis(host="redis", port=6379)

@app.post("/v1/generate/pin/dispatch")
def dispatch(payload: dict):
    job_payload = {
        "job_id": str(uuid.uuid4()),
        "data": payload.get("data", {})
    }
    queue.lpush("generate_pin_queue", json.dumps(job_payload))
    return {
        "status": "queued",
        "job_id": job_payload["job_id"]
    }