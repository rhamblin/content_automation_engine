from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel, ITextProvider


class WordPressChannel(IDistributionChannel):
    """WordPress distribution channel via REST API.

    Raises:
        ConnectionError: When WordPress API is unreachable.
        RuntimeError: When WordPress API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    PROVIDER_NAME = "wordpress"

    DEFAULT_PROMPT = """
Role:
You are a professional recipe content creator for ChefExotic.com.
Your persona is a warm, friendly home cook (housewife style) who writes in an inviting, comforting, family-oriented tone.

Goal:
Generate a fully formatted, SEO-optimized recipe post for a given keyword (#KEYWORD).
The output must be returned as valid JSON with styled HTML suitable for WordPress visual editors (Elementor or Astra theme).

Output Schema (must always use this format):
{
  "title": "SEO-optimized recipe title",
  "content": "Full styled HTML ready for WordPress visual or Elementor editor"
}

Formatting Rules:
- Wrap all content inside:
  <div class="recipe-content" style="font-family: Arial, sans-serif; color:#333; line-height:1.6; max-width:860px; margin:auto;"> ... </div>
- Use semantic HTML tags: <h2>, <h3>, <p>, <ul>, <ol>, <table>, <a>, <div>
- Inline-style all key elements:
  • Headings: font-size 26 to 28px; margin-top 20 to 24px
  • Paragraphs: font-size 16px
  • Amazon buttons uses this style: style="display: inline-block; background: #ff9900; color: #111; padding: 10px 16px; border-radius: 999px; font-weight: 700 bold; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  • Tables must use <table class="chefexotic-table"> with standard borders and padding
- Include emoji icons to add warmth to headings and list items (e.g., 🍫 🧁 💕)
- Never use Markdown or plaintext formatting.
- Ensure all affiliate links include rel="nofollow noopener sponsored"

Content Structure (must appear in this order):
1. Friendly Introduction 🍫
2. "Jump to Recipe" button
3. One image using the provided URL (if available) with alt text set to the keyword
4. Ingredients list with icons
5. Equipment Needed (with Amazon affiliate "Check price on Amazon" CTAs)
6. Step-by-Step Instructions with icons
7. Health Benefits
8. Nutritional Value Table
9. Serving Suggestions
10. ChefExotic Tips
11. Perfect For (occasions/audiences)
12. Amazon Product Comparison Table
13. Friendly Conclusion

Compliance:
- Include FTC disclosure near all affiliate links:
  <p style="font-size:12px; color:#666;">Disclosure: As an Amazon Associate I earn from qualifying purchases.
  If you click a link and make a purchase, I may receive a commission at no extra cost to you.</p>
- Must be compliant with Google AdSense, Amazon Associates, and ClickBank guidelines.
- Avoid making medical or health claims beyond general benefits.

SEO & Style:
- Integrate keywords naturally.
- Use engaging, family-friendly tone; sound like you are chatting with friends in your kitchen.
- Match tone and structure similar to:
  https://chefexotic.com/main-dishes/baked-pork-tenderloin/

Output:
Return ONLY valid JSON in the exact schema above, containing styled HTML with sectioned formatting for WordPress or Elementor editors.
"""

    def __init__(
        self,
        site_url: str,
        username: str,
        app_password: str,
        text_provider: ITextProvider,
    ):
        self.logger = AppLogger(__name__)
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2/posts"
        self.text_provider = text_provider

    @property
    def system_prompt(self) -> str:
        return self.DEFAULT_PROMPT

    def render_content(self, source: Any, text_data: dict, style=None) -> dict:
        """Render WordPress content via text provider.

        Args:
            source: Not used for WordPress (pass None)
            text_data: Dict with niche, keyword, image_url
            style: Optional VisualStyle for field schema

        Returns:
            Dict with title, content (HTML), etc.
        """
        return self.text_provider.generate_text(
            niche=text_data.get("niche", ""),
            keyword=text_data.get("keyword", ""),
            channel=self,
            style=style,
            image_url=text_data.get("image_url", ""),
        )

    def publish(
        self,
        title: str,
        content: str,
        media_id: int | None = None,
        status: str = "draft",
    ) -> dict:
        """Publish content to WordPress."""
        post_data: dict = {
            "title": title,
            "content": content,
            "status": status,
        }

        if media_id:
            post_data["featured_media"] = media_id

        self.logger.info(f"Publishing to WordPress: {title}")

        try:
            response = requests.post(
                self.api_url,
                json=post_data,
                auth=HTTPBasicAuth(self.username, self.app_password),
                timeout=30,
            )
        except requests.RequestException as e:
            raise ConnectionError(f"WordPress API unreachable: {e}") from e

        if response.status_code >= 400:
            raise RuntimeError(
                f"WordPress API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        if "id" not in data:
            raise ValueError("WordPress response missing post ID")

        return {
            "post_id": str(data["id"]),
            "url": data.get("link", ""),
            "status": data.get("status", "unknown"),
        }
