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
        persona_prompt: str = "",
        audience_prompt: str = "",
        image_base64: str | None = None,
        blog_url: str = "",
    ) -> TitleGenResult:
        """Generate title/description/alt_text via LLM provider."""
        try:
            result = self.llm.generate(
                niche=niche,
                keyword=keyword,
                channel=self.channel,
                persona_prompt=persona_prompt or None,
                audience_prompt=audience_prompt or None,
                image_base64=image_base64,
                blog_url=blog_url,
            )
        except (ConnectionError, ValueError) as e:
            logger.error(f"LLM error for '{keyword}': {e}")
            return TitleGenResult(error=f"LLM call failed for '{keyword}': {e}")

        options = self._parse_result(result)
        if not options:
            return TitleGenResult(error=f"No options parsed for '{keyword}'")
        return TitleGenResult(options=options)

    @staticmethod
    def _parse_result(result: dict | list) -> list[TitleOption]:
        """Parse LLM dict/list response into TitleOptions."""
        items = result if isinstance(result, list) else [result]

        return [
            TitleOption(
                title=item.get("title", ""),
                description=item.get("description", ""),
                reasoning=item.get("reasoning", ""),
                alt_text=item.get("alt_text", ""),
            )
            for item in items
        ]
