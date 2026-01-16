from abc import ABC, abstractmethod
from typing import AsyncIterator
from contextlib import asynccontextmanager


class IDatabase(ABC):
    @abstractmethod
    @asynccontextmanager
    async def session(self) -> AsyncIterator:
        """Get a database session"""
        yield

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection"""
        pass
