from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.contracts.database_models import Project, IntegrationProfile
from common.repositories._base_tenant_scoped_repository import BaseTenantScopedRepository


class ProjectRepository(BaseTenantScopedRepository[Project]):
    """Repository for Project aggregate (includes integration profiles)."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, Project, tenant_id)

    async def add(self, name: str) -> Project:
        project = Project(tenant_id=self._tenant_id, name=name)
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return project

    async def get_by_id_with_profiles(self, id: UUID, include_only_active: bool = True) -> Optional[Project]:
        if include_only_active:
            load_opt = selectinload(Project.integration_profiles.and_(IntegrationProfile.is_active == True))
        else:
            load_opt = selectinload(Project.integration_profiles)

        stmt = (
            select(Project)
            .options(load_opt)
            .where(Project.tenant_id == self._tenant_id, Project.external_id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Project]:
        stmt = select(Project).where(Project.tenant_id == self._tenant_id, Project.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, include_only_active: bool = True) -> List[Project]:
        stmt = select(Project).where(Project.tenant_id == self._tenant_id)
        if include_only_active:
            stmt = stmt.where(Project.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_integration_profile(self, profile: IntegrationProfile) -> IntegrationProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def get_integration_profiles(self, project_id: UUID, include_only_active: bool = True) -> List[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id,
            IntegrationProfile.project_id == project_id
        )
        if include_only_active:
            stmt = stmt.where(IntegrationProfile.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_integration_profile_by_id(self, profile_id: UUID) -> Optional[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id,
            IntegrationProfile.external_id == profile_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_integration_profile(
        self, project_id: UUID, niche_id: UUID, channel_id: UUID
    ) -> Optional[IntegrationProfile]:
        stmt = select(IntegrationProfile).where(
            IntegrationProfile.tenant_id == self._tenant_id,
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
