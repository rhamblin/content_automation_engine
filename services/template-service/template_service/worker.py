import asyncio
from common.app_logger import AppLogger
from common.contracts.messages import LocalOutputMessage, LocalInputMessage
from common.providers import registry


class TemplateServiceWorker:
    """Template Worker Description"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop - this example processes messages with message type of LocalMessage"""
        self.logger.info("TemplateServiceWorker started.")

        while True:
            try:
                data: LocalInputMessage = (
                    await self.registry.get_message_broker().consume(LocalInputMessage)
                )

                if data:
                    contents = data.message
                    self.logger.info(f"Received message: {data}")

                    message = LocalOutputMessage(
                        message=f"Message Received. Hello from {self.__class__.__name__ }! For record, your message was {contents}"
                    ).chain_from(data)

                    await self.registry.get_message_broker().publish(message)
                    self.logger.info(f"Published response message!")
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
