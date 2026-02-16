"""Title-generator workflow contracts and service."""

from common.workflows.title_generator.title_generator_request import TitleGenRequest
from common.workflows.title_generator.title_generator_response import TitleGenResult, TitleOption
from common.workflows.title_generator.title_generator_service import TitleGeneratorService

__all__ = ["TitleGeneratorService", "TitleGenRequest", "TitleGenResult", "TitleOption"]
