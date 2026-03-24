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
        audience_prompt: str | None = None,
        blog_url: str = "",
        product: bool = False,
        image_base64: str | None = None,
        ingredient_image: Image.Image | None = None,
    ) -> PinResult:
        """Generate text via LLM, render pin, return result."""
        text_data = self.llm.generate(
            niche=niche,
            keyword=keyword,
            channel=self.channel,
            style=style,
            locale=locale,
            persona_prompt=persona_prompt,
            audience_prompt=audience_prompt,
            blog_url=blog_url,
            image_base64=image_base64,
        )

        logger.info(f"Style: {style.name} | Title: {text_data.get('title')}")

        render_kwargs = dict(
            source=source_image,
            text_data=text_data,
            style=style,
            brand_text=brand_text,
            product=product,
            ingredient_image=ingredient_image,
        )
        if product:
            src_w, src_h = source_image.size
            aspect = src_h / src_w
            render_kwargs["width"] = 1000
            render_kwargs["height"] = int(1000 * aspect)

        pin_image = self.channel.render_content(**render_kwargs)

        return PinResult(
            image=pin_image,
            keyword=keyword,
            style_name=style.name,
            title=text_data.get("title"),
        )
