from fastapi import FastAPI
from redis import Redis
import json
import uuid

app = FastAPI()
queue = Redis(host="redis", port=6379)

@app.post("/projects/{project_id}/integration_profiles/{profile_id}/generate")
def dispatch(project_id: str, profile_id: str, payload: dict):
    job_payload = {
        "job_id": str(uuid.uuid4()),
        "data": payload.get("data", {})
    }
    job_payload["integration_profile_id"] = profile_id
    queue.lpush("generate_post_queue", json.dumps(job_payload))
    return {
        "status": "queued",
        "job_id": job_payload["job_id"]
    }
