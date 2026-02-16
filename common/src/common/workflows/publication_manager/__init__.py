"""Publication-manager workflow contracts and service."""

from common.workflows.publication_manager.publication_manager_request import PublicationRequest
from common.workflows.publication_manager.publication_manager_response import PinEvaluation

__all__ = ["PublicationManagerService", "PublicationRequest", "PinEvaluation"]


def __getattr__(name: str):
    if name == "PublicationManagerService":
        from common.workflows.publication_manager.publication_manager_service import (
            PublicationManagerService,
        )

        return PublicationManagerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
