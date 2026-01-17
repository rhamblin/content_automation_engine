"""Tests for NicheRepository custom methods."""
import pytest
from common.contracts.database_models import Keyword


class TestNicheRepository:

    @pytest.mark.asyncio
    async def test_get_by_title(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        await niche_repo.add(tenant_id=tenant.id, title="Unique Niche")

        result = await niche_repo.get_by_title(tenant.id, "Unique Niche")

        assert result is not None
        assert result.title == "Unique Niche"

    @pytest.mark.asyncio
    async def test_get_by_id_with_keywords(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Niche With Keywords")
        await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="keyword1"))
        await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="keyword2"))

        result = await niche_repo.get_by_id_with_keywords(niche.external_id)

        assert result is not None
        assert len(result.keywords) == 2

    @pytest.mark.asyncio
    async def test_get_active_niches(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        n1 = await niche_repo.add(tenant_id=tenant.id, title="Active Niche")
        n2 = await niche_repo.add(tenant_id=tenant.id, title="Inactive Niche")
        await niche_repo.deactivate(n2.external_id)

        results = await niche_repo.get_active_niches(tenant.id)

        titles = [n.title for n in results]
        assert "Active Niche" in titles
        assert "Inactive Niche" not in titles

    @pytest.mark.asyncio
    async def test_add_keyword(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")

        keyword = await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="new term"))

        assert keyword.id is not None
        assert keyword.term == "new term"

    @pytest.mark.asyncio
    async def test_get_keywords(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="term1"))
        await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="term2"))

        results = await niche_repo.get_keywords(niche.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_active_keywords(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        k1 = await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="active"))
        k2 = await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="inactive"))
        await niche_repo.deactivate_keyword(k2.id)

        results = await niche_repo.get_active_keywords(niche.id)

        terms = [k.term for k in results]
        assert "active" in terms
        assert "inactive" not in terms

    @pytest.mark.asyncio
    async def test_get_keyword_by_term(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="findme"))

        result = await niche_repo.get_keyword_by_term(niche.id, "findme")

        assert result is not None
        assert result.term == "findme"

    @pytest.mark.asyncio
    async def test_deactivate_keyword(self, niche_repo, sample_tenant):
        tenant = sample_tenant
        niche = await niche_repo.add(tenant_id=tenant.id, title="Test Niche")
        keyword = await niche_repo.add_keyword(Keyword(niche_id=niche.id, term="todeactivate"))

        result = await niche_repo.deactivate_keyword(keyword.id)

        assert result is True
        fetched = await niche_repo.get_keyword_by_id(keyword.id)
        assert fetched.is_active is False
