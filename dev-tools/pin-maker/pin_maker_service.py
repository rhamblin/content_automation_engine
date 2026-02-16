"""Pin-maker business logic — no file I/O."""

from PIL import Image

from common.app_logger import AppLogger
from common.contracts.interfaces.distribution_channel import IDistributionChannel
from common.contracts.interfaces.llm_provider import ILLMProvider
from common.contracts.models.persona import Persona
from common.providers.distribution_channel.pinterest import STYLES

from .models import PinResult

logger = AppLogger(__name__)


class PinMakerService:
    """Pure transform: source image + keyword → rendered pin."""

    def __init__(
        self,
        llm: ILLMProvider,
        channel: IDistributionChannel,
        persona: Persona,
    ):
        self.llm = llm
        self.channel = channel
        self.persona = persona

    def make_pin(
        self,
        source_image: Image.Image,
        keyword: str,
        niche: str,
        locale: str,
        style_name: str,
        brand_text: str,
    ) -> PinResult:
        """Generate text via LLM, render pin, return result."""
        style = STYLES[style_name]

        text_data = self.llm.generate(
            niche=niche,
            keyword=keyword,
            channel=self.channel,
            persona=self.persona,
            style=style,
            locale=locale,
        )

        logger.info(f"Style: {style_name} | Title: {text_data.get('title')}")

        pin_image = self.channel.render_content(
            source=source_image,
            text_data=text_data,
            style=style,
            brand_text=brand_text,
        )

        return PinResult(
            image=pin_image,
            keyword=keyword,
            style_name=style_name,
            title=text_data.get("title"),
        )

    @staticmethod
    def list_styles() -> dict:
        """Return available style names and descriptions."""
        return {name: style.description for name, style in STYLES.items()}
