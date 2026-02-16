"""Promotion-manager workflow contracts and service."""

from common.workflows.promotion_manager.promotion_manager_request import PromotionRequest
from common.workflows.promotion_manager.promotion_manager_response import (
    CampaignEvaluation,
    CampaignInfo,
)

__all__ = [
    "PromotionManagerService",
    "PromotionRequest",
    "CampaignInfo",
    "CampaignEvaluation",
]


def __getattr__(name: str):
    if name == "PromotionManagerService":
        from common.workflows.promotion_manager.promotion_manager_service import (
            PromotionManagerService,
        )

        return PromotionManagerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
