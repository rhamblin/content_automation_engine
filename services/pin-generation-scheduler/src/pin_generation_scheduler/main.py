import time
import requests
import threading
from schedule import repeat, every, run_pending

@repeat(every(5).seconds)
def fire_dispatcher_in_thread():
    t = threading.Thread(target=fire_dispatcher, daemon=True)
    t.start()

def fire_dispatcher():
    print("Fired!", flush=True)
    
    url = "http://pin-dispatcher:80/v1/generate/pin/dispatch"
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