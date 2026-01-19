from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator


class IDatabase(ABC):
    @abstractmethod
    @asynccontextmanager
    async def get_session(self) -> AsyncIterator:
        """Get a database session"""
        yield

    @abstractmethod
    async def close_connection(self) -> None:
        """Close the database connection"""
        pass
