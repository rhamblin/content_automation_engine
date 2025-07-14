from redis import Redis
import json

queue = Redis(host="redis", port=6379)

def process_message():
    while True:
        result = queue.blpop("generate_pin_queue", timeout=0)  # 0 = wait forever

        if result:
            queue_name, message = result
            try:
                data = json.loads(message)
                job_id = data.get("job_id")
                niche = data.get("niche")
                payload = data.get("data", {})

                print(f"[{job_id}] Processing pin for niche: {niche} with data: {payload}", flush=True)

                # Insert your pin generation logic here
                # For example: generate_pin(niche=niche, data=payload)

            except Exception as e:
                print(f"[ERROR] Failed to process message: {message} - {e}", flush=True)

if __name__ == "__main__":
    process_message()