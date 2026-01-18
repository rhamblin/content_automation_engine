"""Tests for BaseTenantScopedRepository inherited methods.

Uses ProjectRepository (BaseTenantScopedRepository) as test subject to verify inherited operations work correctly.
"""
import pytest


class TestBaseTenantScopedRepositoryCRUD:
    """Test inherited operations from BaseTenantScopedRepository."""

    @pytest.mark.asyncio
    async def test_get_all_by_tenant_filters_correctly(self, project_repo, tenant_repo):
        tenant1 = await tenant_repo.add(title="Tenant 1")
        tenant2 = await tenant_repo.add(title="Tenant 2")

        await project_repo.add(tenant_id=tenant1.id, name="Project A")
        await project_repo.add(tenant_id=tenant1.id, name="Project B")
        await project_repo.add(tenant_id=tenant2.id, name="Project C")

        results = await project_repo.get_all_by_tenant(tenant1.id)

        assert len(results) == 2
        assert all(p.tenant_id == tenant1.id for p in results)

    @pytest.mark.asyncio
    async def test_get_all_by_tenant_respects_pagination(self, project_repo, sample_tenant):
        tenant = sample_tenant
        for i in range(5):
            await project_repo.add(tenant_id=tenant.id, name=f"Project {i}")

        results = await project_repo.get_all_by_tenant(tenant.id, limit=2, offset=1)

        assert len(results) == 2
