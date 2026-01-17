"""Tests for TenantRepository custom methods."""
import pytest
from common.contracts.database_models import TenantsChannels


class TestTenantRepository:

    @pytest.mark.asyncio
    async def test_get_by_title(self, tenant_repo):
        await tenant_repo.add(title="Unique Tenant")

        result = await tenant_repo.get_by_title("Unique Tenant")

        assert result is not None
        assert result.title == "Unique Tenant"

    @pytest.mark.asyncio
    async def test_get_by_title_returns_none(self, tenant_repo):
        result = await tenant_repo.get_by_title("Nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_users(self, tenant_repo, user_repo):
        tenant = await tenant_repo.add(title="Tenant With Users")
        user = await user_repo.add(email="user@test.com")
        await tenant_repo.add_user_to_tenant(tenant.id, user.id, "admin")

        result = await tenant_repo.get_by_id_with_users(tenant.external_id)

        assert result is not None
        assert len(result.tenants_users) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_with_channels(self, tenant_repo, channel_repo):
        tenant = await tenant_repo.add(title="Tenant With Channels")
        channel = await channel_repo.add(identifier="tiktok")
        tenant_channel = TenantsChannels(tenant_id=tenant.id, channel_id=channel.id)
        await tenant_repo.add_channel_to_tenant(tenant_channel)

        result = await tenant_repo.get_by_id_with_channels(tenant.external_id)

        assert result is not None
        assert len(result.tenants_channels) == 1

    @pytest.mark.asyncio
    async def test_add_user_to_tenant(self, tenant_repo, user_repo):
        tenant = await tenant_repo.add(title="Test Tenant")
        user = await user_repo.add(email="member@test.com")

        tenant_user = await tenant_repo.add_user_to_tenant(tenant.id, user.id, "member")

        assert tenant_user.tenant_id == tenant.id
        assert tenant_user.user_id == user.id
        assert tenant_user.role == "member"

    @pytest.mark.asyncio
    async def test_remove_user_from_tenant(self, tenant_repo, user_repo):
        tenant = await tenant_repo.add(title="Test Tenant")
        user = await user_repo.add(email="toremove@test.com")
        await tenant_repo.add_user_to_tenant(tenant.id, user.id, "member")

        result = await tenant_repo.remove_user_from_tenant(tenant.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_tenant_channels(self, tenant_repo, channel_repo):
        tenant = await tenant_repo.add(title="Test Tenant")
        channel1 = await channel_repo.add(identifier="youtube")
        channel2 = await channel_repo.add(identifier="instagram")
        await tenant_repo.add_channel_to_tenant(TenantsChannels(tenant_id=tenant.id, channel_id=channel1.id))
        await tenant_repo.add_channel_to_tenant(TenantsChannels(tenant_id=tenant.id, channel_id=channel2.id))

        results = await tenant_repo.get_tenant_channels(tenant.id)

        assert len(results) == 2
