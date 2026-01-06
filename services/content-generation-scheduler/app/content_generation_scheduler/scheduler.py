import time
import requests
import threading
import logging
from schedule import repeat, every, run_pending
from common.observability.logging_config import configure_logging

logger = logging.getLogger(__name__)

@repeat(every(15).seconds)
def fire_dispatcher_in_thread():
    t = threading.Thread(target=fire_dispatcher, daemon=True)
    t.start()

def fire_dispatcher():
    logger.info("Fired!")

    url = "http://content-generation-dispatcher:80/v1/projects/00000000-0000-0000-0000-000000000003/integration_profiles/00000000-0000-0000-0000-000000000007/generate"
    body = {}
    response = requests.post(url, json=body, timeout=5)
    response_data = response.json()

    if response.ok:
        logger.info(f'Fired a dispatcher call correctly: {response_data['job_id']}')
    else:
        logger.error('Fired a dispatcher call incorrectly')

configure_logging()    
while True:
    run_pending()
    time.sleep(1)