"""Tests for UserRepository custom methods."""
import pytest
from uuid import uuid4
from common.contracts.database_models import UsersIdentityProviders


class TestUserRepository:

    @pytest.mark.asyncio
    async def test_get_by_email(self, user_repo):
        await user_repo.add(email="findme@test.com")

        result = await user_repo.get_by_email("findme@test.com")

        assert result is not None
        assert result.email == "findme@test.com"

    @pytest.mark.asyncio
    async def test_get_by_email_returns_none(self, user_repo):
        result = await user_repo.get_by_email("nonexistent@test.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_identity_providers(self, user_repo):
        user = await user_repo.add(email="withproviders@test.com")
        provider = UsersIdentityProviders(
            user_id=user.id,
            identity_provider="google",
            identity_provider_user_id=uuid4()
        )
        await user_repo.add_identity_provider(provider)

        result = await user_repo.get_by_id_with_identity_providers(user.external_id)

        assert result is not None
        assert len(result.users_identity_providers) == 1

    @pytest.mark.asyncio
    async def test_get_by_identity_provider(self, user_repo):
        user = await user_repo.add(email="provider@test.com")
        provider_user_id = uuid4()
        provider = UsersIdentityProviders(
            user_id=user.id,
            identity_provider="github",
            identity_provider_user_id=provider_user_id
        )
        await user_repo.add_identity_provider(provider)

        result = await user_repo.get_by_identity_provider("github", provider_user_id)

        assert result is not None
        assert result.email == "provider@test.com"

    @pytest.mark.asyncio
    async def test_get_active_users(self, user_repo):
        user1 = await user_repo.add(email="active1@test.com")
        user2 = await user_repo.add(email="active2@test.com")
        await user_repo.deactivate(user2.external_id)

        results = await user_repo.get_active_users()

        emails = [u.email for u in results]
        assert "active1@test.com" in emails
        assert "active2@test.com" not in emails

    @pytest.mark.asyncio
    async def test_deactivate(self, user_repo):
        user = await user_repo.add(email="todeactivate@test.com")

        result = await user_repo.deactivate(user.external_id)

        assert result is True
        fetched = await user_repo.get_by_id(user.external_id)
        assert fetched.is_active is False

    @pytest.mark.asyncio
    async def test_get_user_tenants(self, user_repo, tenant_repo):
        user = await user_repo.add(email="multitenent@test.com")
        tenant1 = await tenant_repo.add(title="Tenant 1")
        tenant2 = await tenant_repo.add(title="Tenant 2")
        await tenant_repo.add_user_to_tenant(tenant1.id, user.id, "admin")
        await tenant_repo.add_user_to_tenant(tenant2.id, user.id, "member")

        results = await user_repo.get_user_tenants(user.id)

        assert len(results) == 2
