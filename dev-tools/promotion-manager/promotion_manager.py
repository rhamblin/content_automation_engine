"""Promotion Manager — orchestrator (all I/O lives here)."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))

from auth import PINTEREST_API_URL, get_access_token
from common.app_logger import AppLogger
from common.evaluators.promotion_evaluator import PromotionThresholds

from config import load_request
from common.workflows.promotion_manager import PromotionManagerService

logger = AppLogger(__name__)


# ── Pinterest Ads API client (I/O) ──────────────────────────────────────────


class PinterestCampaignClient:
    """Pinterest Ads API client — read/write operations only."""

    def __init__(self, access_token: str):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_ad_accounts(self) -> list[dict]:
        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts", headers=self.headers
        )
        if not response.ok:
            logger.error(f"Failed to fetch ad accounts: {response.status_code}")
            return []
        return response.json().get("items", [])

    def get_campaigns(
        self, ad_account_id: str, status_filter: list[str] | None = None
    ) -> list[dict]:
        params = {}
        if status_filter:
            params["entity_statuses"] = ",".join(status_filter)

        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers=self.headers,
            params=params,
        )
        if not response.ok:
            logger.error(f"Failed to fetch campaigns: {response.status_code}")
            return []
        return response.json().get("items", [])

    def get_campaign_analytics(
        self, ad_account_id: str, campaign_ids: list[str], days: int = 7
    ) -> dict:
        if not campaign_ids:
            return {}

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        response = requests.get(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns/analytics",
            headers=self.headers,
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "campaign_ids": ",".join(campaign_ids),
                "columns": "CAMPAIGN_NAME,TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
                "granularity": "TOTAL",
            },
        )

        if not response.ok:
            logger.error(f"Failed to fetch analytics: {response.status_code}")
            return {}

        result = {}
        for item in response.json():
            campaign_id = item.get("CAMPAIGN_ID")
            if campaign_id:
                result[campaign_id] = {
                    "impressions": item.get("TOTAL_IMPRESSION", 0) or 0,
                    "clicks": item.get("TOTAL_CLICKTHROUGH", 0) or 0,
                    "spend": item.get("SPEND_IN_DOLLAR", 0) or 0,
                    "ctr": item.get("CTR", 0) or 0,
                    "cpc": item.get("ECPC_IN_DOLLAR", 0) or 0,
                }
        return result

    def update_campaign_status(
        self, ad_account_id: str, campaign_id: str, status: str
    ) -> bool:
        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "status": status}],
        )
        if not response.ok:
            logger.error(f"Failed to update campaign: {response.status_code}")
            return False
        logger.info(f"Campaign {campaign_id} status updated to {status}")
        return True

    def update_campaign_budget(
        self, ad_account_id: str, campaign_id: str, daily_spend_cap: float
    ) -> bool:
        microdollars = int(daily_spend_cap * 1_000_000)
        response = requests.patch(
            f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
            headers={**self.headers, "Content-Type": "application/json"},
            json=[{"id": campaign_id, "daily_spend_cap": microdollars}],
        )
        if not response.ok:
            logger.error(f"Failed to update budget: {response.status_code}")
            return False
        logger.info(f"Campaign {campaign_id} daily budget updated to ${daily_spend_cap:.2f}")
        return True


# ── Display helpers ──────────────────────────────────────────────────────────


def print_campaigns_table(campaigns: list) -> None:
    if not campaigns:
        print("No campaigns found.")
        return

    print(
        f"\n{'Name':<40} {'Status':<10} {'Budget':<10} {'Impr':<10} "
        f"{'Clicks':<8} {'CTR':<8} {'CPC':<8} {'Spend':<10}"
    )
    print("-" * 114)

    for c in campaigns:
        print(
            f"{c.name[:39]:<40} "
            f"{c.status[:8]:<10} "
            f"${c.daily_spend_cap:<9.2f} "
            f"{c.impressions:<10,} "
            f"{c.clicks:<8,} "
            f"{c.ctr:<7.2f}% "
            f"${c.cpc:<7.2f} "
            f"${c.spend:<9.2f}"
        )


def print_evaluation_table(results: list) -> None:
    if not results:
        print("No actions recommended.")
        return

    print(
        f"\n{'Campaign':<35} {'Action':<12} {'CTR':<8} {'CPC':<8} {'Reason'}"
    )
    print("-" * 120)

    for r in results:
        m = r.metrics
        print(
            f"{r.campaign_name[:34]:<35} "
            f"{r.action:<12} "
            f"{m.get('ctr', 0):<7.2f}% "
            f"${m.get('cpc', 0):<7.2f} "
            f"{r.reason}"
        )


# ── Execute actions ──────────────────────────────────────────────────────────


def execute_actions(
    client: PinterestCampaignClient,
    ad_account_id: str,
    results: list,
    budget_increase_pct: float = 25,
) -> None:
    """Execute recommended actions on campaigns."""
    for r in results:
        if r.action == "pause":
            client.update_campaign_status(ad_account_id, r.campaign_id, "PAUSED")
        elif r.action == "remove":
            client.update_campaign_status(ad_account_id, r.campaign_id, "PAUSED")
            logger.info(f"Campaign {r.campaign_id} removed (paused + flagged)")
        elif r.action == "adjust":
            adjustment = r.payload.get("adjustment", "")
            if adjustment == "increase_budget" and r.current_budget > 0:
                new_budget = r.current_budget * (1 + budget_increase_pct / 100)
                client.update_campaign_budget(ad_account_id, r.campaign_id, new_budget)


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    data_file = Path(__file__).parent / "data" / "example.json"
    request = load_request(data_file)

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Auth error: {e}")
        sys.exit(1)

    client = PinterestCampaignClient(access_token)

    # Get ad account
    ad_accounts = client.get_ad_accounts()
    if not ad_accounts:
        logger.error("No ad accounts found")
        sys.exit(1)

    ad_account_id = ad_accounts[0]["id"]
    logger.info(f"Using ad account: {ad_account_id}")

    thresholds = PromotionThresholds(
        target_cpc=request.target_cpc,
        high_ctr=request.high_ctr,
        low_ctr=request.low_ctr,
        min_impressions=request.min_impressions,
    )
    service = PromotionManagerService(thresholds)

    if request.command == "list":
        status_filter = None if request.status_filter == "all" else [request.status_filter.upper()]
        campaigns_raw = client.get_campaigns(ad_account_id, status_filter)
        campaign_ids = [c["id"] for c in campaigns_raw]
        analytics = client.get_campaign_analytics(ad_account_id, campaign_ids, request.days)

        campaigns = [
            service.build_campaign_info(c, analytics.get(c["id"], {}))
            for c in campaigns_raw
        ]

        if request.output_json:
            print(json.dumps([vars(c) for c in campaigns], indent=2))
        else:
            print_campaigns_table(campaigns)

    elif request.command == "evaluate":
        campaigns_raw = client.get_campaigns(ad_account_id, ["ACTIVE"])
        campaign_ids = [c["id"] for c in campaigns_raw]
        analytics = client.get_campaign_analytics(ad_account_id, campaign_ids, request.days)

        results = []
        for c in campaigns_raw:
            info = service.build_campaign_info(c, analytics.get(c["id"], {}))
            evaluation = service.evaluate_campaign(info, request.days)
            results.append(evaluation)

        if request.actionable:
            results = [r for r in results if r.action != "none"]

        if request.output_json:
            print(json.dumps([vars(r) for r in results], indent=2))
        else:
            actions = {}
            for r in results:
                actions[r.action] = actions.get(r.action, 0) + 1

            print(f"\nEvaluated {len(results)} active campaigns:")
            for action, count in sorted(actions.items()):
                print(f"  {action}: {count}")

            print_evaluation_table(results)

        if request.execute:
            actionable = [r for r in results if r.action != "none"]
            if actionable:
                logger.info(f"Executing {len(actionable)} action(s)...")
                execute_actions(client, ad_account_id, actionable, request.budget_increase)
            else:
                logger.info("No actions to execute.")
        elif any(r.action != "none" for r in results):
            print("\n[DRY RUN] Set \"execute\": true in data/example.json to apply changes.")

    elif request.command == "pause":
        client.update_campaign_status(ad_account_id, request.campaign_id, "PAUSED")

    elif request.command == "start":
        client.update_campaign_status(ad_account_id, request.campaign_id, "ACTIVE")

    elif request.command == "budget":
        client.update_campaign_budget(ad_account_id, request.campaign_id, request.budget_amount)


if __name__ == "__main__":
    main()
