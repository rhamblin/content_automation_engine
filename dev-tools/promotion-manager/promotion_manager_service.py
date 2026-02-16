"""Promotion-manager business logic — no file I/O."""

from common.app_logger import AppLogger
from common.evaluators import PromotionEvaluator
from common.evaluators.promotion_evaluator import PromotionThresholds

from models import CampaignEvaluation, CampaignInfo

logger = AppLogger(__name__)


class PromotionManagerService:
    """Pure evaluation: campaign metrics → action recommendations."""

    def __init__(self, thresholds: PromotionThresholds):
        self.evaluator = PromotionEvaluator(thresholds)

    def build_campaign_info(self, campaign: dict, metrics: dict) -> CampaignInfo:
        """Build a CampaignInfo from raw API data."""
        return CampaignInfo(
            id=campaign["id"],
            name=campaign.get("name", "Unknown"),
            status=campaign.get("status", "UNKNOWN"),
            daily_spend_cap=campaign.get("daily_spend_cap", 0) / 1_000_000,
            lifetime_spend_cap=campaign.get("lifetime_spend_cap", 0) / 1_000_000,
            impressions=metrics.get("impressions", 0),
            clicks=metrics.get("clicks", 0),
            spend=metrics.get("spend", 0),
            ctr=metrics.get("ctr", 0),
            cpc=metrics.get("cpc", 0),
        )

    def evaluate_campaign(self, info: CampaignInfo, days: int) -> CampaignEvaluation:
        """Evaluate a single campaign and return recommendation."""
        metrics = {
            "impressions": info.impressions,
            "clicks": info.clicks,
            "spend": info.spend,
            "ctr": info.ctr,
            "cpc": info.cpc,
            "days_active": days,
            "lifetime_budget": info.lifetime_spend_cap,
        }
        evaluation = self.evaluator.evaluate(metrics)
        return CampaignEvaluation(
            campaign_id=info.id,
            campaign_name=info.name,
            action=evaluation.action.value,
            reason=evaluation.reason,
            current_budget=info.daily_spend_cap,
            metrics=evaluation.metrics,
            payload=evaluation.payload,
        )
