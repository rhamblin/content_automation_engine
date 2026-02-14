from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel, ILLMProvider


class WordPressChannel(IDistributionChannel):
    """WordPress distribution channel via REST API.

    Raises:
        ConnectionError: When WordPress API is unreachable.
        RuntimeError: When WordPress API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    PROVIDER_NAME = "wordpress"

    DEFAULT_PROMPT = """
You are Marge, a stay-at-home mom cooking for a large family and sharing recipes with friends.
Your tone is happy, friendly and family-oriented. You speak like you're chatting with a friend in your kitchen.

NEVER start with greetings like "Welcome to my site" or "Hello friends". Jump straight into the recipe.
Start the content with: "Here's a {keyword} recipe" in a warm, conversational way.

Generate a fully formatted, SEO-optimized recipe post.
Output must be valid JSON with styled HTML suitable for WordPress visual editors (Elementor or Astra theme).

Output Schema:
{{
  "title": "Keyword Recipe (e.g., Lava Cake Recipe, Plantain Bites Recipe)",
  "content": "Full styled HTML ready for WordPress visual or Elementor editor"
}}

Formatting Rules:
- Wrap content in: <div class="recipe-content" style="font-family: Arial, sans-serif; color:#333; line-height:1.6; max-width:860px; margin:auto;">
- Use semantic HTML: <h2>, <h3>, <p>, <ul>, <ol>, <table>, <a>, <div>
- Inline-style elements:
  * Headings: font-size 26-28px; margin-top 20-24px
  * Paragraphs: font-size 16px
  * Amazon buttons: style="display: inline-block; background: #ff9900; color: #111; padding: 10px 16px; border-radius: 999px; font-weight: 700; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.15);"
  * Tables: <table class="chefexotic-table"> with borders and padding
- Never use Markdown or plaintext formatting
- Affiliate links must use actual Amazon affiliate tag: {amazon_tag}
  Example: https://www.amazon.com/dp/ASIN?tag={amazon_tag}
  All affiliate links must include rel="nofollow noopener sponsored"

Title Rules:
- The title MUST be the keyword followed by "Recipe" (e.g., "Lava Cake Recipe", "Plantain Bites Recipe")
- This ensures the keyword is the first thing on the page for SEO

Content Structure:
1. First element: <h2 style="font-size:28px; margin-top:24px;">{keyword} Recipe</h2> - this is the SEO anchor
2. Warm personal intro (2-3 sentences, no greetings, start with "Here's a {keyword} recipe...")
3. "Jump to Recipe" button
4. DO NOT include the featured image - it is auto-injected by WordPress. Only include additional images if there are multiple.
5. Ingredients list
6. Equipment Needed (with Amazon affiliate CTAs using tag={amazon_tag})
7. Step-by-Step Instructions
8. Health Benefits
9. Nutritional Value Table
10. Serving Suggestions
11. Tips
12. Perfect For (occasions/audiences)
13. Amazon Products Recommended table (NOT "Amazon Product Comparison")
14. Marge's Final Thoughts (NOT "Conclusion" or "Final Conclusion")

Amazon Product Rules:
- NEVER show prices. Instead use a price tier indicator:
  * Under $10: $ (Budget-Friendly)
  * $11-$99: $$ (Mid-Range)
  * $100-$999: $$$ (Premium)
  * $1000+: $$$$ (Luxury)
- Column headers: Product | Price Range | Link
- The link column should say "Check Price on Amazon" as clickable affiliate link
- Use actual Amazon affiliate tag: {amazon_tag}
- Table heading must be "Amazon Products Recommended" not "Amazon Product Comparison"

Compliance:
- FTC disclosure near affiliate links: <p style="font-size:12px; color:#666;">Disclosure: As an Amazon Associate I earn from qualifying purchases.</p>
- Compliant with Google AdSense, Amazon Associates, ClickBank guidelines
- No medical/health claims beyond general benefits

SEO:
- Integrate keywords naturally
- The keyword + "Recipe" must be the first H2 on the page

Output: Return ONLY valid JSON in the schema above.
"""

    def __init__(
        self,
        site_url: str,
        username: str,
        app_password: str,
        llm: ILLMProvider,
        amazon_tag: str = "",
    ):
        self.logger = AppLogger(__name__)
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2/posts"
        self.llm = llm
        self.amazon_tag = amazon_tag

    @property
    def system_prompt(self) -> str:
        return self.DEFAULT_PROMPT.replace("{amazon_tag}", self.amazon_tag)

    def render_content(self, source: Any, text_data: dict, style=None) -> dict:
        """Render WordPress content via LLM provider.

        Args:
            source: Not used for WordPress (pass None)
            text_data: Dict with niche, keyword, image_url, persona, locale
            style: Optional VisualStyle for field schema

        Returns:
            Dict with title, content (HTML), etc.
        """
        return self.llm.generate(
            niche=text_data.get("niche", ""),
            keyword=text_data.get("keyword", ""),
            channel=self,
            persona=text_data.get("persona"),
            style=style,
            locale=text_data.get("locale", "en"),
            image_url=text_data.get("image_url", ""),
        )

    def _get_or_create_tags(self, tag_names: list[str]) -> list[int]:
        """Get or create WordPress tags by name, return list of tag IDs."""
        auth = HTTPBasicAuth(self.username, self.app_password)
        tags_url = f"{self.site_url}/wp-json/wp/v2/tags"
        tag_ids = []

        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            try:
                # Search for existing tag
                resp = requests.get(tags_url, params={"search": name}, auth=auth, timeout=10)
                if resp.ok and resp.json():
                    for tag in resp.json():
                        if tag["name"].lower() == name.lower():
                            tag_ids.append(tag["id"])
                            break
                    else:
                        # Exact match not found, create it
                        resp = requests.post(tags_url, json={"name": name}, auth=auth, timeout=10)
                        if resp.ok:
                            tag_ids.append(resp.json()["id"])
                else:
                    # No results, create tag
                    resp = requests.post(tags_url, json={"name": name}, auth=auth, timeout=10)
                    if resp.ok:
                        tag_ids.append(resp.json()["id"])
            except requests.RequestException:
                self.logger.warning(f"Failed to create/find tag: {name}")

        return tag_ids

    def publish(
        self,
        title: str,
        content: str,
        media_id: int | None = None,
        status: str = "draft",
        tags: list[str] | None = None,
    ) -> dict:
        """Publish content to WordPress."""
        post_data: dict = {
            "title": title,
            "content": content,
            "status": status,
        }

        if media_id:
            post_data["featured_media"] = media_id

        if tags:
            tag_ids = self._get_or_create_tags(tags)
            if tag_ids:
                post_data["tags"] = tag_ids

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
