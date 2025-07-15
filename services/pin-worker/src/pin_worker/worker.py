from redis import Redis
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from db_core.db_sync import get_db_session
from db_core.models.niche import Niche
from db_core.models.keyword import Keyword
import time
import json



broker = Redis(host="redis", port=6379)

def process_message():
    while True:
        result = broker.blpop("generate_pin_queue", timeout=0)  # 0 = wait forever

        if result:
            queue_name, message = result
            try:
                data = json.loads(message)
                job_id = data.get("job_id")
                payload = data.get("data", {})

                print(f"[{job_id}] Processing job with data: {payload}", flush=True)

                generate_pins(job_id)

                print(f"[{job_id}] Finished Processing job with data: {payload} \n\n", flush=True)

            except Exception as e:
                print(f"[ERROR] Failed to process message: {message} - {e}", flush=True)

def generate_pins(job_id):
    niches = get_niches()

    for niche in niches:
        keywords = niche.keywords
        for value in keywords:
            kw = value.keyword
            asset = get_asset(kw)
            title = generate_pin_title(niche.name, kw)
            description = generate_pin_description(niche.name, kw)
            metadata = generate_metadata()

            save_pin(niche.name, kw, title, description, asset, metadata)
            publish_event(job_id)

def publish_event(job_id):
    payload = {"job_id": job_id}
    msg = json.dumps(payload)
    broker.rpush("pin_events", msg)

def get_all_niches():
    db = get_db_session()
    result = db.execute(select(Niche).order_by(Niche.name).options(selectinload(Niche.keywords)))
    return result.scalars().all()

def get_niches():
    # e.g. fetch from DB or API
    return get_all_niches()

def get_asset(keyword):
    # lookup or generate image URL
    return f"https://cdn.example.com/assets/{keyword}.jpg"

def generate_pin_title(niche, keyword):
    return f"{niche}: {keyword} Inspiration"

def generate_pin_description(niche, keyword):
    return f"Explore amazing {keyword} tips in our {niche} series."

def generate_metadata():
    return {"created_by": "worker-v1", "timestamp": time.time()}

def save_pin(niche, keyword, title, desc, asset, metadata):
    print(f"  · Saving pin [{niche}/{keyword}]", flush=True)

if __name__ == "__main__":
    process_message()