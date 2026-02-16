"""Debug Pinterest API responses."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from pinterest_auth.auth import PINTEREST_API_URL, get_access_token

access_token = get_access_token()
headers = {"Authorization": f"Bearer {access_token}"}

# 1. Get one pin
print("=== FETCHING PINS ===")
response = requests.get(f"{PINTEREST_API_URL}/pins", headers=headers, params={"page_size": 1})
print(f"Status: {response.status_code}")
pins = response.json()
print(json.dumps(pins, indent=2)[:1000])

if pins.get("items"):
    pin_id = pins["items"][0]["id"]

    # 2. Get pin analytics
    print(f"\n=== PIN ANALYTICS ({pin_id}) ===")
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=13)

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK",
    }
    response = requests.get(f"{PINTEREST_API_URL}/pins/{pin_id}/analytics", headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2)[:2000])

# 3. Get ad accounts
print("\n=== AD ACCOUNTS ===")
response = requests.get(f"{PINTEREST_API_URL}/ad_accounts", headers=headers)
print(f"Status: {response.status_code}")
ad_accounts = response.json()
print(json.dumps(ad_accounts, indent=2)[:1000])

if ad_accounts.get("items"):
    ad_account_id = ad_accounts["items"][0]["id"]

    # 4. Get ads
    print(f"\n=== ADS ({ad_account_id}) ===")
    response = requests.get(f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ads", headers=headers)
    print(f"Status: {response.status_code}")
    ads = response.json()
    print(json.dumps(ads, indent=2)[:1000])

    if ads.get("items"):
        ad_ids = [a["id"] for a in ads["items"][:2]]

        # 5. Get ad analytics
        print(f"\n=== AD ANALYTICS ({ad_ids}) ===")
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "ad_ids": ",".join(ad_ids),
            "columns": "TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,REPIN_1,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
            "granularity": "DAY",
        }
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ads/analytics",
            headers=headers,
            params=params,
        )
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2)[:2000])
