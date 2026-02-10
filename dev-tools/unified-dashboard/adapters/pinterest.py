"""Pinterest adapter for unified dashboard."""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from .base import PlatformAdapter, AccountMetrics, ContentItem, DailyMetrics

# Add get-pin-ids to path for auth module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "get-pin-ids"))

PINTEREST_API_URL = "https://api.pinterest.com/v5"


class PinterestAdapter(PlatformAdapter):
    """Pinterest API adapter."""

    PLATFORM_NAME = "pinterest"
    PLATFORM_COLOR = "#E60023"

    ORGANIC_METRICS = ["IMPRESSION", "SAVE", "PIN_CLICK", "OUTBOUND_CLICK"]
    CAMPAIGN_METRICS = ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR"]

    def __init__(self, credentials_path: str, account_config: dict):
        super().__init__(credentials_path, account_config)
        self.access_token = None
        self.headers = {}

    def authenticate(self) -> bool:
        """Load access token from credentials."""
        try:
            # Try to use the auth module from get-pin-ids
            from auth import get_access_token
            self.access_token = get_access_token()
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            return True
        except Exception as e:
            print(f"Pinterest auth failed: {e}")
            return False

    def fetch_metrics(self, niche: str, days: int = 14) -> AccountMetrics:
        """Fetch aggregated metrics for Pinterest account."""
        if not self.access_token:
            if not self.authenticate():
                return AccountMetrics(
                    platform=self.PLATFORM_NAME,
                    niche=niche,
                    account_name=self.account_name,
                    error="Authentication failed",
                )

        metrics = AccountMetrics(
            platform=self.PLATFORM_NAME,
            niche=niche,
            account_name=self.account_name,
            days=days,
        )

        # Fetch organic data
        content_items = self.fetch_content_items(days)
        metrics.content_items = content_items

        # Aggregate organic metrics
        daily_agg = {}
        for item in content_items:
            for dm in item.daily:
                if dm.date not in daily_agg:
                    daily_agg[dm.date] = DailyMetrics(date=dm.date)
                daily_agg[dm.date].impressions += dm.impressions
                daily_agg[dm.date].engagements += dm.engagements
                daily_agg[dm.date].clicks += dm.clicks
                daily_agg[dm.date].saves += dm.saves

            metrics.impressions += item.totals.get("impressions", 0)
            metrics.engagements += item.totals.get("saves", 0) + item.totals.get("clicks", 0)
            metrics.clicks += item.totals.get("outbound_clicks", 0)
            metrics.reach += item.totals.get("impressions", 0)  # Pinterest doesn't have separate reach

        metrics.daily = sorted(daily_agg.values(), key=lambda x: x.date)

        # Fetch paid data
        campaigns = self._fetch_campaign_data(days)
        metrics.campaigns = campaigns

        for c in campaigns:
            metrics.spend += c.get("spend", 0)
            metrics.paid_impressions += c.get("impressions", 0)
            metrics.paid_clicks += c.get("clicks", 0)

        return metrics

    def fetch_content_items(self, days: int = 14) -> list[ContentItem]:
        """Fetch pins with their metrics."""
        pins = self._fetch_all_pins()
        items = []

        print(f"  Fetching analytics for {len(pins)} pins...")

        for i, pin in enumerate(pins):
            pin_id = pin.get("id")
            analytics = self._fetch_pin_analytics(pin_id, days)

            if analytics:
                daily_data = analytics.get("all", {}).get("daily_metrics", [])
                daily_metrics = []
                totals = {"impressions": 0, "saves": 0, "clicks": 0, "outbound_clicks": 0}

                for day in daily_data:
                    dm = DailyMetrics(
                        date=day.get("date", ""),
                        impressions=day.get("IMPRESSION", 0),
                        saves=day.get("SAVE", 0),
                        clicks=day.get("PIN_CLICK", 0),
                        engagements=day.get("SAVE", 0) + day.get("PIN_CLICK", 0),
                    )
                    daily_metrics.append(dm)
                    totals["impressions"] += dm.impressions
                    totals["saves"] += dm.saves
                    totals["clicks"] += dm.clicks
                    totals["outbound_clicks"] += day.get("OUTBOUND_CLICK", 0)

                items.append(ContentItem(
                    id=pin_id,
                    title=pin.get("title", "Untitled"),
                    url=f"https://pinterest.com/pin/{pin_id}",
                    created_at=pin.get("created_at", ""),
                    content_type="pin",
                    totals=totals,
                    daily=daily_metrics,
                ))

            if (i + 1) % 20 == 0:
                print(f"    Processed {i + 1}/{len(pins)} pins")

            time.sleep(0.3)

        return items

    def _fetch_all_pins(self) -> list[dict]:
        """Fetch all pins from account."""
        pins = []
        bookmark = None

        while True:
            params = {"page_size": 100}
            if bookmark:
                params["bookmark"] = bookmark

            response = requests.get(
                f"{PINTEREST_API_URL}/pins",
                headers=self.headers,
                params=params,
            )

            if not response.ok:
                print(f"Failed to fetch pins: {response.status_code}")
                break

            data = response.json()
            pins.extend(data.get("items", []))
            bookmark = data.get("bookmark")

            if not bookmark:
                break

        return pins

    def _fetch_pin_analytics(self, pin_id: str, days: int) -> dict | None:
        """Fetch analytics for a single pin."""
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        response = requests.get(
            f"{PINTEREST_API_URL}/pins/{pin_id}/analytics",
            headers=self.headers,
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "metric_types": ",".join(self.ORGANIC_METRICS),
            },
        )

        if not response.ok:
            return None

        return response.json()

    def _fetch_campaign_data(self, days: int) -> list[dict]:
        """Fetch campaign/paid data."""
        # Get ad accounts
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts",
            headers=self.headers,
        )

        if not response.ok:
            return []

        ad_accounts = response.json().get("items", [])
        if not ad_accounts:
            return []

        ad_account_id = ad_accounts[0]["id"]
        campaigns = []

        # Fetch campaigns
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers=self.headers,
        )

        if not response.ok:
            return []

        campaign_list = response.json().get("items", [])
        campaign_ids = [c["id"] for c in campaign_list]

        if not campaign_ids:
            return []

        # Fetch analytics
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns/analytics",
            headers=self.headers,
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "campaign_ids": ",".join(campaign_ids),
                "columns": "CAMPAIGN_NAME,TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,SPEND_IN_DOLLAR",
                "granularity": "TOTAL",
            },
        )

        if not response.ok:
            return []

        for row in response.json():
            campaign_info = next(
                (c for c in campaign_list if c["id"] == row.get("CAMPAIGN_ID")),
                {}
            )
            campaigns.append({
                "id": row.get("CAMPAIGN_ID"),
                "name": campaign_info.get("name", "Unknown"),
                "status": campaign_info.get("status", "UNKNOWN"),
                "impressions": row.get("TOTAL_IMPRESSION", 0) or 0,
                "clicks": row.get("TOTAL_CLICKTHROUGH", 0) or 0,
                "spend": row.get("SPEND_IN_DOLLAR", 0) or 0,
            })

        return campaigns
