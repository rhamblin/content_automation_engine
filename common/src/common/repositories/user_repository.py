from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import User, UsersIdentityProviders, TenantsUsers
from common.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User aggregate (includes identity providers)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_identity_providers(self, id: UUID) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.users_identity_providers))
            .where(User.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identity_provider(self, provider: str, provider_user_id: UUID) -> Optional[User]:
        stmt = (
            select(User)
            .join(UsersIdentityProviders)
            .where(
                UsersIdentityProviders.identity_provider == provider,
                UsersIdentityProviders.identity_provider_user_id == provider_user_id
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        stmt = select(User).where(User.is_active == True).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_identity_provider(self, identity_provider: UsersIdentityProviders) -> UsersIdentityProviders:
        self._session.add(identity_provider)
        await self._session.flush()
        return identity_provider

    async def get_identity_providers(self, user_id: UUID) -> List[UsersIdentityProviders]:
        stmt = select(UsersIdentityProviders).where(UsersIdentityProviders.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_tenants(self, user_id: UUID) -> List[TenantsUsers]:
        stmt = select(TenantsUsers).where(TenantsUsers.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate(self, id: UUID) -> bool:
        user = await self.get_by_id(id)
        if user:
            user.is_active = False
            await self._session.flush()
            return True
        return False
