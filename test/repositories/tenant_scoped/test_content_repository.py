"""Tests for ContentRepository custom methods."""
import pytest


class TestContentRepository:

    @pytest.mark.asyncio
    async def test_get_by_id_with_renders(self, content_repo, render_repo, sample_content, sample_niche, sample_keyword):
        content = sample_content
        niche = sample_niche
        keyword = sample_keyword
        await render_repo.add(
            tenant_id=content.tenant_id,
            content_id=content.id,
            niche_id=niche.id,
            keyword_id=keyword.id
        )

        result = await content_repo.get_by_id_with_renders(content.external_id)

        assert result is not None
        assert len(result.renders) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_with_publications(self, content_repo, publication_repo, sample_content, sample_channel):
        content = sample_content
        channel = sample_channel
        await publication_repo.add(
            tenant_id=content.tenant_id,
            channel_id=channel.id,
            content_id=content.id
        )

        result = await content_repo.get_by_id_with_publications(content.external_id)

        assert result is not None
        assert len(result.publications) == 1

    @pytest.mark.asyncio
    async def test_get_by_keyword(self, content_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Content 1")
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Content 2")

        results = await content_repo.get_by_keyword(keyword.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_niche(self, content_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Content 1")
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Content 2")

        results = await content_repo.get_by_niche(niche.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_title(self, content_repo, sample_tenant, sample_niche, sample_keyword):
        tenant = sample_tenant
        niche = sample_niche
        keyword = sample_keyword
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Python Tutorial")
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Python Guide")
        await content_repo.add(tenant_id=tenant.id, niche_id=niche.id, keyword_id=keyword.id, title="Java Tutorial")

        results = await content_repo.search_by_title(tenant.id, "Python")

        assert len(results) == 2
        assert all("Python" in c.title for c in results)
