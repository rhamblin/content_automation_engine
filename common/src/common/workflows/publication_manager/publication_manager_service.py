"""Publication-manager business logic — no file I/O."""

from common.app_logger import AppLogger
from common.evaluators import PublicationEvaluator
from common.evaluators.publication_evaluator import PublicationThresholds

from common.workflows.publication_manager.publication_manager_response import PinEvaluation

logger = AppLogger(__name__)


class PublicationManagerService:
    """Pure evaluation: pin metrics → action recommendations."""

    def __init__(self, thresholds: PublicationThresholds):
        self.evaluator = PublicationEvaluator(thresholds)

    def evaluate_pin(self, pin_id: str, title: str, link: str, metrics: dict) -> PinEvaluation:
        """Evaluate a single pin's metrics and return recommendation."""
        evaluation = self.evaluator.evaluate(metrics)
        return PinEvaluation(
            pin_id=pin_id,
            title=title,
            link=link,
            action=evaluation.action.value,
            reason=evaluation.reason,
            metrics=evaluation.metrics,
        )
