from fastapi import FastAPI
from redis import Redis
import json
import uuid
from common.constants import constants

app = FastAPI(
    title="Post Dispatcher",
    description="This is what submits a job to the broker signalling a post should be generated",
    )

queue = Redis(host="redis", port=6379)

@app.post("/v1/projects/{project_id}/integration_profiles/{profile_id}/generate")
def dispatch(project_id: str, profile_id: str, payload: dict):
    job_payload = {
        "job_id": str(uuid.uuid4()),
        "project_id": project_id,
        "integration_profile_id": profile_id,
        "data": payload.get("data", {}),
    }
    queue.lpush(constants.GENERATE_POST_QUEUE_NAME, json.dumps(job_payload))
    return {"status": "queued", "job_id": job_payload["job_id"]}