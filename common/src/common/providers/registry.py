from common.contracts.interfaces import (
    IBlobStorage,
    IDatabase,
    IDistributionChannel,
    ILLMProvider,
    IMessageBroker,
)


class ProviderRegistry:
    def __init__(
        self,
        database: IDatabase | None = None,
        message_broker: IMessageBroker | None = None,
        blob_storage: IBlobStorage | None = None,
        llm_providers: dict[str, ILLMProvider] | None = None,
        distribution_channels: dict[str, IDistributionChannel] | None = None,
    ):
        self.database = database
        self.blob_storage = blob_storage
        self.message_broker = message_broker
        self.llm_providers = llm_providers or {}
        self.channels = distribution_channels or {}

    def get_database(self) -> IDatabase:
        if self.database is None:
            raise LookupError("Database not available in this worker's registry")
        return self.database

    def get_blob_storage(self) -> IBlobStorage:
        if self.blob_storage is None:
            raise LookupError("Blob storage not available in this worker's registry")
        return self.blob_storage

    def get_message_broker(self) -> IMessageBroker:
        if self.message_broker is None:
            raise LookupError("Message broker not available in this worker's registry")
        return self.message_broker

    def get_llm(self, key: str = "") -> ILLMProvider:
        if not key and len(self.llm_providers) >= 1:
            return list(self.llm_providers.values())[0]
        elif key not in self.llm_providers:
            raise LookupError(f"LLM provider '{key}' not available in this worker's registry")
        return self.llm_providers[key]

    def get_channel(self, key: str) -> IDistributionChannel:
        if key not in self.channels:
            raise LookupError(f"Channel '{key}' not available in this worker's registry")
        return self.channels[key]

    async def shutdown(self):
        if self.message_broker:
            await self.message_broker.close()
        if self.database:
            await self.database.close_connection()
