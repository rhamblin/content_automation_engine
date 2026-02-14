"""Evaluates paid promotion metrics and recommends actions."""

from dataclasses import dataclass, field

from common.contracts.database_models.enums import PromotionActionTaken


@dataclass
class PromotionThresholds:
    """Configurable thresholds for promotion evaluation."""

    target_cpc: float = 2.00           # $ - CPC above this is too expensive
    min_impressions: int = 1000
    high_ctr: float = 2.0             # % - performing well enough to increase spend
    low_ctr: float = 0.5              # % - underperforming
    maturity_days: int = 5            # days before evaluating CPC trend
    budget_exhausted_pct: float = 95  # % of budget spent = exhausted


@dataclass
class PromotionEvaluation:
    """Result of evaluating a promotion."""

    action: PromotionActionTaken
    reason: str
    metrics: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


class PromotionEvaluator:
    """Evaluates paid campaign metrics and returns a recommended PromotionActionTaken."""

    def __init__(self, thresholds: PromotionThresholds | None = None):
        self.thresholds = thresholds or PromotionThresholds()

    def evaluate(self, metrics: dict) -> PromotionEvaluation:
        """Evaluate promotion metrics and recommend an action.

        Args:
            metrics: dict with keys: impressions, clicks, spend, cpc, ctr,
                     days_active, daily_budget, lifetime_budget.

        Returns:
            PromotionEvaluation with action, reason, and optional payload.
        """
        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        spend = metrics.get("spend", 0)
        ctr = metrics.get("ctr", 0)
        cpc = metrics.get("cpc", 0)
        days_active = metrics.get("days_active", 0)
        lifetime_budget = metrics.get("lifetime_budget", 0)

        computed = {
            "impressions": impressions,
            "clicks": clicks,
            "spend": round(spend, 2),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "days_active": days_active,
        }

        # Zero clicks after significant spend
        if impressions >= self.thresholds.min_impressions and clicks == 0:
            return PromotionEvaluation(
                action=PromotionActionTaken.REMOVE,
                reason=f"Zero clicks after {impressions:,} impressions - dead creative",
                metrics=computed,
            )

        # Budget exhausted
        if lifetime_budget > 0:
            budget_used_pct = (spend / lifetime_budget) * 100
            if budget_used_pct >= self.thresholds.budget_exhausted_pct:
                if cpc <= self.thresholds.target_cpc and ctr >= self.thresholds.high_ctr:
                    return PromotionEvaluation(
                        action=PromotionActionTaken.ADJUST,
                        reason=f"Budget exhausted but performing well (CPC ${cpc:.2f}, CTR {ctr:.2f}%) - increase budget",
                        metrics=computed,
                        payload={"adjustment": "increase_budget"},
                    )
                return PromotionEvaluation(
                    action=PromotionActionTaken.REMOVE,
                    reason=f"Budget exhausted with poor performance (CPC ${cpc:.2f}, CTR {ctr:.2f}%)",
                    metrics=computed,
                )

        # Not enough data yet
        if impressions < self.thresholds.min_impressions:
            return PromotionEvaluation(
                action=PromotionActionTaken.NONE,
                reason=f"Insufficient data ({impressions} impressions < {self.thresholds.min_impressions})",
                metrics=computed,
            )

        # CPC too high after maturity period
        if cpc > self.thresholds.target_cpc and days_active >= self.thresholds.maturity_days:
            return PromotionEvaluation(
                action=PromotionActionTaken.PAUSE,
                reason=f"CPC ${cpc:.2f} > target ${self.thresholds.target_cpc:.2f} after {days_active} days",
                metrics=computed,
            )

        # CPC too high but still maturing
        if cpc > self.thresholds.target_cpc and days_active < self.thresholds.maturity_days:
            return PromotionEvaluation(
                action=PromotionActionTaken.NONE,
                reason=f"CPC ${cpc:.2f} above target but only {days_active} days active - still optimizing",
                metrics=computed,
            )

        # Low CTR
        if ctr < self.thresholds.low_ctr:
            return PromotionEvaluation(
                action=PromotionActionTaken.PAUSE,
                reason=f"CTR {ctr:.2f}% < {self.thresholds.low_ctr}%",
                metrics=computed,
            )

        # High CTR + CPC within target - increase spend
        if ctr >= self.thresholds.high_ctr and cpc <= self.thresholds.target_cpc:
            return PromotionEvaluation(
                action=PromotionActionTaken.ADJUST,
                reason=f"Strong performance (CTR {ctr:.2f}%, CPC ${cpc:.2f}) - increase budget",
                metrics=computed,
                payload={"adjustment": "increase_budget"},
            )

        # Everything within acceptable range
        return PromotionEvaluation(
            action=PromotionActionTaken.NONE,
            reason=f"Within targets (CTR {ctr:.2f}%, CPC ${cpc:.2f})",
            metrics=computed,
        )
