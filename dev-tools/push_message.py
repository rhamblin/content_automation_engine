import redis
from datetime import UTC, datetime
from common.messaging_contracts import ContentGenerationRequested 

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

payload = ContentGenerationRequested(
    job_id="job_123",
    project_id="project_456",
    integration_profile_id="profile_789",
    data={"key": "value"},
)

r.xadd(ContentGenerationRequested.message_name(), payload.to_json())

print("Message pushed")
