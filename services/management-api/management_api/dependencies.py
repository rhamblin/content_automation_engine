from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncSession:
    async with request.app.state.registry.get_database().get_session() as session:
        yield session
