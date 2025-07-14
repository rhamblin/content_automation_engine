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
                payload = data.get("data", {})

                print(f"[{job_id}] Processing job with data: {payload}", flush=True)

                generate_pins(job_id)
            except Exception as e:
                print(f"[ERROR] Failed to process message: {message} - {e}", flush=True)

def generate_pins(job_id):
    niches = get_niches()

    for niche in niches:
        keywords = niches.keywords
        for kw in keywords:
            asset = get_asset(kw)
            title = generate_pin_title(niche, kw)
            description = generate_pin_description(niche, kw)
            metadata = generate_metadata()

            save_pin(niche, kw, title, description, asset, metadata)
            publish_event()
def publish_event(job_id):
    payload = {"job_id": job_id}
    msg = json.dumps(payload)
    queue.rpush("pin_events", msg)

def get_niches():
    # e.g. fetch from DB or API
    return [
        {"name": "travel", "keywords": ["beach", "mountains"]},
        {"name": "food",   "keywords": ["pasta", "sushi"]},
    ]

def get_asset(keyword):
    # lookup or generate image URL
    return f"https://cdn.example.com/assets/{keyword}.jpg"

def generate_pin_title(niche, keyword):
    return f"{niche['name'].title()}: {keyword.title()} Inspiration"

def generate_pin_description(niche, keyword):
    return f"Explore amazing {keyword} tips in our {niche['name']} series."

def generate_metadata():
    return {"created_by": "worker-v1", "timestamp": time.time()}

def save_pin(niche, keyword, title, desc, asset, metadata):
    print(f"  · Saving pin [{niche['name']}/{keyword}]", flush=True)

if __name__ == "__main__":
    process_message()