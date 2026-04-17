"""News aggregator orchestrator — fetch RSS feeds and display/save results."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from linkedin.news_aggregator.config import load_config
from common.workflows.linkedin.news_aggregator import NewsAggregatorService

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "news_input.json"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    logger.info("Loading config...")
    config = load_config(DATA_FILE)
    logger.info(
        "Config loaded — %d sources, max %d articles each",
        len(config.request.sources),
        config.request.max_per_source,
    )

    service = NewsAggregatorService()
    result = service.aggregate(config.request)

    # --- display results ---
    print(f"\n{'=' * 80}")
    print(f"  NEWS AGGREGATOR — {len(result.articles)} articles fetched")
    print(f"{'=' * 80}\n")

    for article in result.articles:
        print(f"  [{article.category}] {article.source_name}")
        print(f"  {article.title}")
        print(f"  {article.url}")
        if article.summary:
            summary = article.summary[:200] + ("..." if len(article.summary) > 200 else "")
            print(f"  {summary}")
        print(f"  Published: {article.published_date}")
        print()

    if result.errors:
        print(f"\n  Errors ({len(result.errors)}):")
        for err in result.errors:
            print(f"    - {err}")
        print()

    # --- save output ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"news_{timestamp}.json"

    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tenant": config.tenant,
        "article_count": len(result.articles),
        "articles": [
            {
                "title": a.title,
                "url": a.url,
                "summary": a.summary,
                "published_date": a.published_date,
                "source_name": a.source_name,
                "category": a.category,
            }
            for a in result.articles
        ],
        "errors": result.errors,
    }

    output_path.write_text(json.dumps(output_data, indent=2))
    logger.info("Results saved to %s", output_path)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as e:
        logger.error(str(e))
        sys.exit(1)
