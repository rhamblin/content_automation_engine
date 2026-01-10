import asyncio
from common.app_logger import AppLogger
from common.contracts import LocalMessage
from common.providers import registry

class TemplateServiceWorker:
    """Template Worker Description"""
    def __init__(
            self, 
            registry: registry.ProviderRegistry):
        self.logger = AppLogger(__name__)
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop - this example processes messages with message type of LocalMessage"""
        message_name = LocalMessage.message_name()
        payload = LocalMessage(message=f"Hello from {self.__class__.__name__ }!")

        while True:
            try:
                result = await self.registry.get_message_broker.publish(message_name, payload.to_json()) #consume or publish?

                if result:
                    _, message = result
                    try:
                        payload = LocalMessage.from_json(message)
                        self.logger.info(f"Received message: {payload.message}")
                    except Exception as e:
                        self.logger.error(f"Failed to process message {message}: {e}")

            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
