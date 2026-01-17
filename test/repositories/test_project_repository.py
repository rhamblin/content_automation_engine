"""Tests for ProjectRepository custom methods."""
import pytest
from common.contracts.database_models import IntegrationProfile


class TestProjectRepository:

    @pytest.mark.asyncio
    async def test_get_by_name(self, project_repo, sample_tenant):
        tenant = sample_tenant
        await project_repo.add(tenant_id=tenant.id, name="Unique Project")

        result = await project_repo.get_by_name(tenant.id, "Unique Project")

        assert result is not None
        assert result.name == "Unique Project"

    @pytest.mark.asyncio
    async def test_get_by_name_returns_none(self, project_repo, sample_tenant):
        tenant = sample_tenant
        result = await project_repo.get_by_name(tenant.id, "Nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_profiles(self, project_repo, niche_repo, channel_repo, sample_tenant):
        tenant = sample_tenant
        project = await project_repo.add(tenant_id=tenant.id, name="Test Project")
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        channel = await channel_repo.add(identifier="test_channel")
        profile = IntegrationProfile(
            project_id=project.id,
            niche_id=niche.id,
            channel_id=channel.id
        )
        await project_repo.add_integration_profile(profile)

        result = await project_repo.get_by_id_with_profiles(project.external_id)

        assert result is not None
        assert len(result.integration_profiles) == 1

    @pytest.mark.asyncio
    async def test_get_active_projects(self, project_repo, sample_tenant):
        tenant = sample_tenant
        p1 = await project_repo.add(tenant_id=tenant.id, name="Active 1")
        p2 = await project_repo.add(tenant_id=tenant.id, name="Inactive")
        await project_repo.deactivate(p2.external_id)

        results = await project_repo.get_active_projects(tenant.id)

        names = [p.name for p in results]
        assert "Active 1" in names
        assert "Inactive" not in names

    @pytest.mark.asyncio
    async def test_get_integration_profile(self, project_repo, niche_repo, channel_repo, sample_tenant):
        tenant = sample_tenant
        project = await project_repo.add(tenant_id=tenant.id, name="Test Project")
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        channel = await channel_repo.add(identifier="some_channel")
        profile = IntegrationProfile(
            project_id=project.id,
            niche_id=niche.id,
            channel_id=channel.id
        )
        await project_repo.add_integration_profile(profile)

        result = await project_repo.get_integration_profile(project.id, niche.id, channel.id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_deactivate(self, project_repo, sample_tenant):
        tenant = sample_tenant
        project = await project_repo.add(tenant_id=tenant.id, name="To Deactivate")

        result = await project_repo.deactivate(project.external_id)

        assert result is True
        fetched = await project_repo.get_by_id(project.external_id)
        assert fetched.is_active is False
