"""Tests for BaseTenantScopedRepository inherited methods.

Uses NicheRepository (BaseTenantScopedRepository) as test subject to verify inherited operations work correctly.
"""
import pytest


class TestBaseTenantScopedRepositoryCRUD:
    """Test inherited operations from BaseTenantScopedRepository."""

    @pytest.mark.asyncio
    async def test_get_all_by_tenant_filters_correctly(self, niche_repo, tenant_repo):
        tenant1 = await tenant_repo.add(title="Tenant 1")
        tenant2 = await tenant_repo.add(title="Tenant 2")

        await niche_repo.add(tenant_id=tenant1.id, title="Niche A")
        await niche_repo.add(tenant_id=tenant1.id, title="Niche B")
        await niche_repo.add(tenant_id=tenant2.id, title="Niche C")

        results = await niche_repo.get_all_by_tenant(tenant1.id)

        assert len(results) == 2
        assert all(n.tenant_id == tenant1.id for n in results)

    @pytest.mark.asyncio
    async def test_get_all_by_tenant_respects_pagination(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        for i in range(5):
            await niche_repo.add(tenant_id=tenant.id, title=f"Niche {i}")

        results = await niche_repo.get_all_by_tenant(tenant.id, limit=2, offset=1)

        assert len(results) == 2
