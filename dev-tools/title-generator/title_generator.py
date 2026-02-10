"""Title Generator - generate titles and descriptions for content using AI."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).parent / "output"

sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import load_dev_settings


SYSTEM_PROMPT = """You are an expert content strategist specializing in creating engaging titles and descriptions for digital content. Your goal is to create content that:
- Captures attention and drives engagement
- Is optimized for the specific platform/channel
- Incorporates the keyword naturally
- Speaks to the target niche audience
- Uses proven copywriting techniques (curiosity, urgency, value proposition)

Always return valid JSON matching the requested format."""


def generate_titles(
    channel: str,
    niche: str,
    keyword: str,
    settings,
    count: int = 3,
    style: str = "mixed",
) -> list[dict]:
    """Generate titles and descriptions using Azure OpenAI."""

    style_guidance = {
        "mixed": "Create a mix of styles: one curiosity-driven, one value-focused, one emotional/story-based.",
        "clickbait": "Use attention-grabbing, curiosity-inducing hooks (but avoid misleading claims).",
        "professional": "Use clear, authoritative, professional tone.",
        "casual": "Use conversational, friendly, relatable tone.",
        "seo": "Prioritize keyword placement and search optimization.",
    }

    user_prompt = f"""Generate {count} unique title and description combinations for the following:

Channel/Platform: {channel}
Niche: {niche}
Target Keyword: {keyword}

Style guidance: {style_guidance.get(style, style_guidance['mixed'])}

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

    headers = {
        "Content-Type": "application/json",
        "api-key": settings.azure_foundry_api_key,
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
        f"{settings.azure_foundry_endpoint}/openai/deployments/gpt-4o/chat/completions?api-version={settings.azure_foundry_api_version}",
        headers=headers,
        json=payload,
    )

    if not response.ok:
        print(f"API Error: {response.status_code} - {response.text}")
        return []

    content = response.json()["choices"][0]["message"]["content"]

    # Parse JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content.strip())


def print_results(results: list[dict], channel: str, niche: str, keyword: str):
    """Print results in formatted output."""
    print(f"\n{'=' * 70}")
    print(f"Channel: {channel} | Niche: {niche} | Keyword: {keyword}")
    print(f"{'=' * 70}")

    for i, item in enumerate(results, 1):
        print(f"\n--- Option {i} ---")
        print(f"\nTitle:\n  {item.get('title', 'N/A')}")
        print(f"\nDescription:\n  {item.get('description', 'N/A')}")
        print(f"\nStrategy:\n  {item.get('reasoning', 'N/A')}")
        print()


def save_results(results: list[dict], channel: str, niche: str, keyword: str, style: str) -> Path:
    """Save results to JSON file in output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{channel}_{timestamp}.json"
    filepath = OUTPUT_DIR / filename

    output = {
        "generated_at": datetime.now().isoformat(),
        "params": {
            "channel": channel,
            "niche": niche,
            "keyword": keyword,
            "style": style,
        },
        "results": results,
    }

    filepath.write_text(json.dumps(output, indent=2))
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Generate titles and descriptions for content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate titles for Pinterest:
    python title_generator.py --channel pinterest --niche "home cooking" --keyword "air fryer recipes"

  Generate for YouTube with SEO focus:
    python title_generator.py --channel youtube --niche fitness --keyword "home workout" --style seo

  Generate 5 options:
    python title_generator.py --channel instagram --niche travel --keyword "budget travel tips" --count 5

  Output as JSON:
    python title_generator.py --channel tiktok --niche beauty --keyword "skincare routine" --json

Styles:
  mixed       - Variety of approaches (default)
  clickbait   - Attention-grabbing hooks
  professional - Clear, authoritative tone
  casual      - Conversational, friendly
  seo         - Keyword-optimized
        """,
    )

    parser.add_argument("--channel", "-c", required=True, help="Platform (pinterest, youtube, instagram, tiktok, blog, etc.)")
    parser.add_argument("--niche", "-n", required=True, help="Content niche (e.g., 'home cooking', 'fitness', 'travel')")
    parser.add_argument("--keyword", "-k", required=True, help="Target keyword to incorporate")
    parser.add_argument("--count", type=int, default=3, help="Number of options to generate (default: 3)")
    parser.add_argument("--style", choices=["mixed", "clickbait", "professional", "casual", "seo"], default="mixed", help="Style of titles (default: mixed)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    settings = load_dev_settings()

    results = generate_titles(
        channel=args.channel,
        niche=args.niche,
        keyword=args.keyword,
        settings=settings,
        count=args.count,
        style=args.style,
    )

    if not results:
        print("Failed to generate titles.")
        sys.exit(1)

    # Save to file
    filepath = save_results(results, args.channel, args.niche, args.keyword, args.style)
    print(f"Saved to: {filepath}")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results, args.channel, args.niche, args.keyword)


if __name__ == "__main__":
    main()
