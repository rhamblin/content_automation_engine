"""Title-generator business logic — no file I/O."""

from common.app_logger import AppLogger
from common.contracts.interfaces.distribution_channel import IDistributionChannel
from common.contracts.interfaces.llm_provider import ILLMProvider
from common.workflows.title_generator.title_generator_response import (
    TitleGenResult,
    TitleOption,
)

logger = AppLogger(__name__)


class TitleGeneratorService:
    """Pure transform: channel + niche + keyword → generated titles via LLM provider."""

    def __init__(self, llm: ILLMProvider, channel: IDistributionChannel):
        self.llm = llm
        self.channel = channel

    def generate(
        self,
        niche: str,
        keyword: str,
        count: int = 1,
        copy_style_prompt: str = "",
        persona_prompt: str = "",
    ) -> TitleGenResult:
        """Generate title/description/alt_text via LLM provider."""
        try:
            result = self.llm.generate(
                niche=niche,
                keyword=keyword,
                channel=self.channel,
                copy_style_prompt=copy_style_prompt or None,
                persona_prompt=persona_prompt or None,
            )
        except (ConnectionError, ValueError) as e:
            logger.error(f"LLM error for '{keyword}': {e}")
            return TitleGenResult(error=str(e))

        # Result is a dict from the LLM — could be a single object or array
        options = self._parse_result(result, count)
        return TitleGenResult(options=options)

    @staticmethod
    def _parse_result(result: dict | list, count: int) -> list[TitleOption]:
        """Parse LLM dict/list response into TitleOptions."""
        # LLM may return a single dict or a list
        items = result if isinstance(result, list) else [result]

        return [
            TitleOption(
                title=item.get("title", ""),
                description=item.get("description", ""),
                reasoning=item.get("reasoning", ""),
                alt_text=item.get("alt_text", ""),
            )
            for item in items[:count]
        ]
