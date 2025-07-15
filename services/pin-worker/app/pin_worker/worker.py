from redis import Redis
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from db_core.db_sync import get_db_session
from db_core.models.niche import Niche
from db_core.models.keyword import Keyword
from db_core.models.pin import Pin

from call_to_gen_ai import generate_pin_title, generate_pin_description

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

                print(f"*"*50, flush=True)

                print(f"[{job_id}] Processing job with data: {payload}", flush=True)

                generate_pins(job_id)

                print(f"[{job_id}] Finished Processing job with data: {payload}", flush=True)

                print(f"*"*50, flush=True)

            except Exception as e:
                print(f"[ERROR] Failed to process message: {message} - {e}", flush=True)

def generate_pins(job_id):
    niches = get_all_niches()

    for niche in niches:
        keywords = niche.keywords
        for value in keywords:
            kw = value.keyword
            asset_url = get_asset_url(kw)
            title = generate_pin_title(niche.name, kw)
            description = generate_pin_description(niche.name, kw)

            pin = Pin(
                title=title,
                description=description,
                keyword_id=value.keyword_id,
                asset_url=asset_url
            )
            print(f"="*50, flush=True)

            save_pin(pin, kw, niche.name)

            print(f"="*50, flush=True)

            publish_event(job_id)

def publish_event(job_id):
    payload = {"job_id": job_id}
    msg = json.dumps(payload)
    broker.rpush("pin_events", msg)

def get_all_niches():
    with get_db_session() as session:
        result = session.execute(select(Niche).order_by(Niche.name).options(selectinload(Niche.keywords)))
        return result.scalars().all()

def get_asset_url(keyword):
    # lookup or generate image URL
    return f"https://cdn.example.com/assets/{keyword}.jpg"

def save_pin(pin: Pin, kw, niche: str):
    print(f"\n\nFor niche -> {niche}\n\n", flush=True)

    print(f"\n\nFor keyword -> {kw}\n\n", flush=True)

    print(f"{pin.to_readable()}", flush=True)

if __name__ == "__main__":
    process_message()