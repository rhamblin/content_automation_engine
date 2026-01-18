from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Project, IntegrationProfile
from common.repositories.base_tenant_scoped_repository import BaseTenantScopedRepository


class ProjectRepository(BaseTenantScopedRepository[Project]):
    """Repository for Project aggregate (includes integration profiles)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)

    async def add(self, tenant_id: UUID, name: str) -> Project:
        project = Project(tenant_id=tenant_id, name=name)
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def get_by_id_with_profiles(self, id: UUID) -> Optional[Project]:
        stmt = (
            select(Project)
            .options(selectinload(Project.integration_profiles))
            .where(Project.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, tenant_id: UUID, name: str) -> Optional[Project]:
        stmt = select(Project).where(Project.tenant_id == tenant_id, Project.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_projects(self, tenant_id: UUID) -> List[Project]:
        stmt = select(Project).where(Project.tenant_id == tenant_id, Project.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_integration_profile(self, profile: IntegrationProfile) -> IntegrationProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def get_integration_profiles(self, project_id: UUID) -> List[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(IntegrationProfile.project_id == project_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_integration_profile_by_id(self, profile_id: UUID) -> Optional[IntegrationProfile]:
        return await self._session.get(IntegrationProfile, profile_id)

    async def get_integration_profile(
        self, project_id: UUID, niche_id: UUID, channel_id: UUID
    ) -> Optional[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.project_id == project_id,
            IntegrationProfile.niche_id == niche_id,
            IntegrationProfile.channel_id == channel_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate(self, id: UUID) -> bool:
        project = await self.get_by_id(id)
        if project:
            project.is_active = False
            await self._session.flush()
            return True
        return False
