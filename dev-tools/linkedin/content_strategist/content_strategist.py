"""Content strategist orchestrator — interactive chat with RAG grounding."""

import logging
import sys
from pathlib import Path

from linkedin.content_strategist.config import load_config
from common.workflows.linkedin.content_strategist import ContentStrategistService

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent / "data" / "strategist_input.json"


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    logger.info("Loading config...")
    config = load_config(DATA_FILE)
    logger.info("Config loaded for tenant: %s", config.tenant)

    service = ContentStrategistService(config.service_config)

    try:
        service.initialize()

        print(f"\n{'=' * 60}")
        print("  LinkedIn Content Strategist")
        print("  Type your idea, draft, or direction.")
        print("  Type 'quit' or 'exit' to end the session.")
        print(f"{'=' * 60}\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("\nEnding session.")
                break

            try:
                response = service.chat(user_input)
                print(f"\nStrategist:\n{response.message}\n")

                if response.annotations:
                    print("  Sources:")
                    for ann in response.annotations:
                        print(f"    - {ann}")
                    print()
            except Exception as e:
                logger.error("Chat error: %s", e)
                print(f"\n  [Error: {e}]\n")

    except KeyboardInterrupt:
        print("\n\nSession interrupted.")
    finally:
        service.cleanup()
        logger.info("Session ended.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as e:
        logger.error(str(e))
        sys.exit(1)
