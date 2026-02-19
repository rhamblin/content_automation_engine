"""Pin-maker business logic — no file I/O."""

from common.app_logger import AppLogger
from common.contracts.interfaces.distribution_channel import IDistributionChannel
from common.contracts.interfaces.llm_provider import ILLMProvider
from common.contracts.models.rendering.visual_style import VisualStyle
from common.workflows.pin_maker.pin_maker_response import PinResult
from PIL import Image

logger = AppLogger(__name__)


class PinMakerService:
    """Pure transform: source image + keyword → rendered pin."""

    def __init__(
        self,
        llm: ILLMProvider,
        channel: IDistributionChannel,
    ):
        self.llm = llm
        self.channel = channel

    def make_pin(
        self,
        source_image: Image.Image,
        keyword: str,
        niche: str,
        locale: str,
        style: VisualStyle,
        brand_text: str,
        persona_prompt: str | None = None,
        copy_style_prompt: str | None = None,
        audience_prompt: str | None = None,
    ) -> PinResult:
        """Generate text via LLM, render pin, return result."""
        text_data = self.llm.generate(
            niche=niche,
            keyword=keyword,
            channel=self.channel,
            style=style,
            locale=locale,
            persona_prompt=persona_prompt,
            copy_style_prompt=copy_style_prompt,
            audience_prompt=audience_prompt,
        )

        logger.info(f"Style: {style.name} | Title: {text_data.get('title')}")

        pin_image = self.channel.render_content(
            source=source_image,
            text_data=text_data,
            style=style,
            brand_text=brand_text,
        )

        return PinResult(
            image=pin_image,
            keyword=keyword,
            style_name=style.name,
            title=text_data.get("title"),
        )
