from .base import BaseRepository
from .tenant_scoped import BaseTenantScopedRepository

# Global repositories (not tenant-scoped)
from .global.tenant_repository import TenantRepository
from .global.user_repository import UserRepository
from .global.channel_repository import ChannelRepository

# Tenant-scoped repositories
from .scoped.project_repository import ProjectRepository
from .scoped.niche_repository import NicheRepository
from .scoped.content_repository import ContentRepository
from .scoped.image_repository import ImageRepository
from .scoped.render_repository import RenderRepository
from .scoped.publication_repository import PublicationRepository
from .scoped.schedule_repository import ScheduleRepository
from .scoped.report_repository import ReportRepository

__all__ = [
    # Base
    "BaseRepository",
    "BaseTenantScopedRepository",
    # Global repositories
    "TenantRepository",
    "UserRepository",
    "ChannelRepository",
    # Tenant-scoped repositories
    "ProjectRepository",
    "NicheRepository",
    "ContentRepository",
    "ImageRepository",
    "RenderRepository",
    "PublicationRepository",
    "ScheduleRepository",
    "ReportRepository",
]
