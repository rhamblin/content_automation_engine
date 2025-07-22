import time
import requests
import threading
from schedule import repeat, every, run_pending

@repeat(every(15).seconds)
def fire_dispatcher_in_thread():
    t = threading.Thread(target=fire_dispatcher, daemon=True)
    t.start()

def fire_dispatcher():
    print("Fired!", flush=True)
    
    url = "http://post-dispatcher:80/v1/projects/00000000-0000-0000-0000-000000000003/integration_profiles/00000000-0000-0000-0000-000000000007/generate"
    body = {}
    response = requests.post(url, json=body, timeout=5)
    response_data = response.json()

    if response.ok:
        print(f'Fired a dispatcher call correctly: {response_data['job_id']}', flush=True)
    else:
        print('Fired a dispatcher call incorrectly', flush=True)
    
while True:
    run_pending()
    time.sleep(1)