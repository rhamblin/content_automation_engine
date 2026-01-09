import redis
from datetime import UTC, datetime

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

r.xadd(
    "activity_report_stream",
    {
        "schedule_id": "manual-dev",
        "schedule_type": "activity_report",
        "scope_type": "tenant",
        "scope_id": "tenant-123",
        "triggered_at": datetime.now(UTC).isoformat()
    }
)

print("Message pushed")
