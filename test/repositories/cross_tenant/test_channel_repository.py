"""Tests for ChannelRepository custom methods."""
import pytest
from common.contracts.database_models import TenantsChannels


class TestChannelRepository:

    @pytest.mark.asyncio
    async def test_get_by_identifier(self, channel_repo):
        await channel_repo.add(identifier="twitter")

        result = await channel_repo.get_by_identifier("twitter")

        assert result is not None
        assert result.identifier == "twitter"

    @pytest.mark.asyncio
    async def test_get_by_identifier_returns_none(self, channel_repo):
        result = await channel_repo.get_by_identifier("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_channels_for_tenant(self, channel_repo, tenant_repo):
        tenant = await tenant_repo.add(title="Test Tenant")
        channel1 = await channel_repo.add(identifier="linkedin")
        channel2 = await channel_repo.add(identifier="facebook")
        await tenant_repo.add_channel_to_tenant(TenantsChannels(tenant_id=tenant.id, channel_id=channel1.id))
        await tenant_repo.add_channel_to_tenant(TenantsChannels(tenant_id=tenant.id, channel_id=channel2.id))

        results = await channel_repo.get_channels_for_tenant(tenant.id)

        assert len(results) == 2
        identifiers = [c.identifier for c in results]
        assert "linkedin" in identifiers
        assert "facebook" in identifiers

    @pytest.mark.asyncio
    async def test_get_or_create_by_identifier_creates(self, channel_repo):
        result = await channel_repo.get_or_create_by_identifier("newchannel")

        assert result is not None
        assert result.identifier == "newchannel"

    @pytest.mark.asyncio
    async def test_get_or_create_by_identifier_returns_existing(self, channel_repo):
        existing = await channel_repo.add(identifier="existing")

        result = await channel_repo.get_or_create_by_identifier("existing")

        assert result.id == existing.id
