"""Title-generator business logic — no file I/O."""

import json

import requests
from common.app_logger import AppLogger

from common.workflows.title_generator.title_generator_response import TitleGenResult, TitleOption

logger = AppLogger(__name__)

SYSTEM_PROMPT = """You are an expert content strategist specializing in creating engaging titles and descriptions for digital content. Your goal is to create content that:
- Captures attention and drives engagement
- Is optimized for the specific platform/channel
- Incorporates the keyword naturally
- Speaks to the target niche audience
- Uses proven copywriting techniques (curiosity, urgency, value proposition)

Always return valid JSON matching the requested format."""

STYLE_GUIDANCE = {
    "mixed": "Create a mix of styles: one curiosity-driven, one value-focused, one emotional/story-based.",
    "clickbait": "Use attention-grabbing, curiosity-inducing hooks (but avoid misleading claims).",
    "professional": "Use clear, authoritative, professional tone.",
    "casual": "Use conversational, friendly, relatable tone.",
    "seo": "Prioritize keyword placement and search optimization.",
}


class TitleGeneratorService:
    """Pure transform: channel + niche + keyword → generated titles."""

    def __init__(self, endpoint: str, api_key: str, api_version: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version

    def generate(
        self, channel: str, niche: str, keyword: str, count: int = 3, style: str = "mixed"
    ) -> TitleGenResult:
        """Generate title/description options via Azure OpenAI."""
        user_prompt = self._build_prompt(channel, niche, keyword, count, style)

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 1500,
        }

        response = requests.post(
            f"{self.endpoint}/openai/deployments/gpt-4o/chat/completions"
            f"?api-version={self.api_version}",
            headers=headers,
            json=payload,
        )

        if not response.ok:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return TitleGenResult(error=f"API {response.status_code}")

        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_response(content)

    @staticmethod
    def _build_prompt(channel: str, niche: str, keyword: str, count: int, style: str) -> str:
        guidance = STYLE_GUIDANCE.get(style) or style or STYLE_GUIDANCE["mixed"]
        return f"""Generate {count} unique title and description combinations for the following:

Channel/Platform: {channel}
Niche: {niche}
Target Keyword: {keyword}

Style guidance: {guidance}

For each combination, provide:
1. A compelling title (optimized for {channel})
2. A description/caption (appropriate length for {channel})
3. A brief explanation of why this approach works

Return as JSON array:
[
  {{
    "title": "The title here",
    "description": "The description/caption here",
    "reasoning": "Brief explanation of the strategy used"
  }}
]

Only return the JSON array, no other text."""

    @staticmethod
    def _parse_response(content: str) -> TitleGenResult:
        """Parse LLM JSON response into TitleGenResult."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        items = json.loads(content.strip())
        options = [
            TitleOption(
                title=item.get("title", ""),
                description=item.get("description", ""),
                reasoning=item.get("reasoning", ""),
                alt_text=item.get("alt_text", ""),
            )
            for item in items
        ]
        return TitleGenResult(options=options)
