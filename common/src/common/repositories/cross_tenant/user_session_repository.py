from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from common.contracts.database_models import UserSession
from common.repositories._base_repository import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession aggregate (cross-tenant, keyed by user)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSession)

    async def add(
        self,
        user_id: UUID,
        refresh_token: str,
        identity_provider: str,
        expires_at: datetime,
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            identity_provider=identity_provider,
            expires_at=expires_at,
        )
        self._session.add(user_session)
        await self._session.flush()
        await self._session.refresh(user_session)
        return user_session

    async def get_active_by_user(self, user_id: UUID) -> Optional[UserSession]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.expires_at > now,
            )
            .order_by(UserSession.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_user(self, user_id: UUID) -> None:
        stmt = delete(UserSession).where(UserSession.user_id == user_id)
        await self._session.execute(stmt)

    async def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = delete(UserSession).where(UserSession.expires_at <= now)
        result = await self._session.execute(stmt)
        return result.rowcount
