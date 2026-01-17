"""Tests for BaseRepository and BaseTenantScopedRepository inherited methods.

Uses TenantRepository (BaseRepository) and ProjectRepository (BaseTenantScopedRepository)
as test subjects to verify inherited CRUD operations work correctly.
"""
import pytest


class TestBaseRepositoryCRUD:
    """Test inherited CRUD operations from BaseRepository."""

    @pytest.mark.asyncio
    async def test_add_creates_entity_with_external_id(self, tenant_repo):
        tenant = await tenant_repo.add(title="New Tenant")

        assert tenant is not None
        assert tenant.external_id is not None
        assert tenant.title == "New Tenant"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(self, tenant_repo):
        tenant = await tenant_repo.add(title="Test Tenant")

        result = await tenant_repo.get_by_id(tenant.external_id)

        assert result is not None
        assert result.external_id == tenant.external_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent(self, tenant_repo):
        from uuid import uuid4
        result = await tenant_repo.get_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_returns_entities(self, tenant_repo):
        await tenant_repo.add(title="Tenant 1")
        await tenant_repo.add(title="Tenant 2")

        results = await tenant_repo.get_all()

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_get_all_respects_limit(self, tenant_repo):
        await tenant_repo.add(title="Tenant 1")
        await tenant_repo.add(title="Tenant 2")
        await tenant_repo.add(title="Tenant 3")

        results = await tenant_repo.get_all(limit=2)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_update_persists_changes(self, tenant_repo):
        tenant = await tenant_repo.add(title="Original Title")
        tenant.title = "Updated Title"

        updated = await tenant_repo.update(tenant)

        assert updated.title == "Updated Title"
        fetched = await tenant_repo.get_by_id(tenant.external_id)
        assert fetched.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_removes_entity(self, tenant_repo):
        tenant = await tenant_repo.add(title="To Delete")

        result = await tenant_repo.delete(tenant.external_id)

        assert result is True
        fetched = await tenant_repo.get_by_id(tenant.external_id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_nonexistent(self, tenant_repo):
        from uuid import uuid4
        result = await tenant_repo.delete(uuid4())

        assert result is False


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
