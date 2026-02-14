"""Evaluates organic publication metrics and recommends actions."""

from dataclasses import dataclass, field

from common.contracts.database_models.enums import PublicationActionTaken


@dataclass
class PublicationThresholds:
    """Configurable thresholds for publication evaluation."""

    min_impressions: int = 500
    high_ctr: float = 1.5          # %
    low_ctr: float = 0.5           # %
    high_save_rate: float = 2.0    # %
    low_save_rate: float = 0.5     # %


@dataclass
class PublicationEvaluation:
    """Result of evaluating a publication."""

    action: PublicationActionTaken
    reason: str
    metrics: dict = field(default_factory=dict)


class PublicationEvaluator:
    """Evaluates organic metrics and returns a recommended PublicationActionTaken."""

    def __init__(self, thresholds: PublicationThresholds | None = None):
        self.thresholds = thresholds or PublicationThresholds()

    def evaluate(self, metrics: dict) -> PublicationEvaluation:
        """Evaluate publication metrics and recommend an action.

        Args:
            metrics: dict with keys: impressions, clicks, saves.

        Returns:
            PublicationEvaluation with action and reason.
        """
        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        saves = metrics.get("saves", 0)

        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        save_rate = (saves / impressions * 100) if impressions > 0 else 0

        computed = {
            "impressions": impressions,
            "clicks": clicks,
            "saves": saves,
            "ctr": round(ctr, 2),
            "save_rate": round(save_rate, 2),
        }

        if impressions < self.thresholds.min_impressions:
            return PublicationEvaluation(
                action=PublicationActionTaken.NONE,
                reason=f"Insufficient data ({impressions} impressions < {self.thresholds.min_impressions})",
                metrics=computed,
            )

        high_ctr = ctr >= self.thresholds.high_ctr
        high_saves = save_rate >= self.thresholds.high_save_rate
        low_ctr = ctr < self.thresholds.low_ctr
        low_saves = save_rate < self.thresholds.low_save_rate

        if high_ctr and high_saves:
            return PublicationEvaluation(
                action=PublicationActionTaken.ADD_TO_CAMPAIGN,
                reason=f"High CTR ({ctr:.2f}%) and high save rate ({save_rate:.2f}%)",
                metrics=computed,
            )

        if low_ctr and high_saves:
            return PublicationEvaluation(
                action=PublicationActionTaken.UPDATE,
                reason=f"Low CTR ({ctr:.2f}%) but high save rate ({save_rate:.2f}%) - content resonates but doesn't compel clicks",
                metrics=computed,
            )

        if low_ctr and low_saves:
            return PublicationEvaluation(
                action=PublicationActionTaken.DELETE,
                reason=f"Low CTR ({ctr:.2f}%) and low save rate ({save_rate:.2f}%)",
                metrics=computed,
            )

        # high_ctr + low_saves, or mid-range values
        return PublicationEvaluation(
            action=PublicationActionTaken.NONE,
            reason=f"Performing adequately (CTR {ctr:.2f}%, save rate {save_rate:.2f}%)",
            metrics=computed,
        )
