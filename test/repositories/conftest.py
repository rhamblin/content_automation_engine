import pytest
import pytest_asyncio

from common.repositories.tenant_repository import TenantRepository
from common.repositories.user_repository import UserRepository
from common.repositories.channel_repository import ChannelRepository
from common.repositories.project_repository import ProjectRepository
from common.repositories.niche_repository import NicheRepository
from common.repositories.content_repository import ContentRepository
from common.repositories.image_repository import ImageRepository
from common.repositories.render_repository import RenderRepository
from common.repositories.publication_repository import PublicationRepository
from common.repositories.schedule_repository import ScheduleRepository
from common.repositories.report_repository import ReportRepository


# Repository fixtures
@pytest.fixture
def tenant_repo(async_db_session):
    return TenantRepository(async_db_session)


@pytest.fixture
def user_repo(async_db_session):
    return UserRepository(async_db_session)


@pytest.fixture
def channel_repo(async_db_session):
    return ChannelRepository(async_db_session)


@pytest.fixture
def project_repo(async_db_session):
    return ProjectRepository(async_db_session)


@pytest.fixture
def niche_repo(async_db_session):
    return NicheRepository(async_db_session)


@pytest.fixture
def content_repo(async_db_session):
    return ContentRepository(async_db_session)


@pytest.fixture
def image_repo(async_db_session):
    return ImageRepository(async_db_session)


@pytest.fixture
def render_repo(async_db_session):
    return RenderRepository(async_db_session)


@pytest.fixture
def publication_repo(async_db_session):
    return PublicationRepository(async_db_session)


@pytest.fixture
def schedule_repo(async_db_session):
    return ScheduleRepository(async_db_session)


@pytest.fixture
def report_repo(async_db_session):
    return ReportRepository(async_db_session)


# Helper fixtures - pytest-asyncio auto-awaits fixture dependencies
@pytest_asyncio.fixture
async def sample_tenant(tenant_repo):
    return await tenant_repo.add(title="Test Tenant")


@pytest_asyncio.fixture
async def sample_user(user_repo):
    return await user_repo.add(email="test@example.com")


@pytest_asyncio.fixture
async def sample_channel(channel_repo):
    return await channel_repo.add(identifier="youtube")


@pytest_asyncio.fixture
async def sample_project(project_repo, sample_tenant):
    # sample_tenant is already awaited by pytest-asyncio
    return await project_repo.add(tenant_id=sample_tenant.id, name="Test Project")


@pytest_asyncio.fixture
async def sample_niche(niche_repo, sample_tenant):
    return await niche_repo.add(tenant_id=sample_tenant.id, title="Test Niche")


@pytest_asyncio.fixture
async def sample_keyword(niche_repo, sample_niche):
    from common.contracts.database_models import Keyword
    keyword = Keyword(niche_id=sample_niche.id, term="test keyword")
    return await niche_repo.add_keyword(keyword)


@pytest_asyncio.fixture
async def sample_content(content_repo, sample_tenant, sample_niche, sample_keyword):
    return await content_repo.add(
        tenant_id=sample_tenant.id,
        niche_id=sample_niche.id,
        keyword_id=sample_keyword.id,
        title="Test Content",
        description="Test Description"
    )


@pytest_asyncio.fixture
async def sample_image(image_repo, sample_tenant, sample_niche, sample_keyword):
    from common.contracts.database_models.enums import ImageKind
    return await image_repo.add(
        tenant_id=sample_tenant.id,
        niche_id=sample_niche.id,
        keyword_id=sample_keyword.id,
        kind=ImageKind.ORIGINAL
    )


@pytest_asyncio.fixture
async def sample_render(render_repo, sample_tenant, sample_content, sample_niche, sample_keyword):
    return await render_repo.add(
        tenant_id=sample_tenant.id,
        content_id=sample_content.id,
        niche_id=sample_niche.id,
        keyword_id=sample_keyword.id
    )


@pytest_asyncio.fixture
async def sample_publication(publication_repo, sample_tenant, sample_channel, sample_content):
    return await publication_repo.add(
        tenant_id=sample_tenant.id,
        channel_id=sample_channel.id,
        content_id=sample_content.id
    )


@pytest_asyncio.fixture
async def sample_schedule(schedule_repo, sample_tenant, sample_niche):
    return await schedule_repo.add(
        tenant_id=sample_tenant.id,
        niche_id=sample_niche.id,
        title="Test Schedule",
        cron_expression="0 9 * * *"
    )
