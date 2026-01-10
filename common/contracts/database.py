from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

class IDatabase(ABC):
    @abstractmethod
    @asynccontextmanager
    def session(self):
        """Get a database session"""
        pass