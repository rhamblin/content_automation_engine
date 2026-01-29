from enum import Enum

from ..messages import (
    ActivityReportRequested,
    CollectAnalyticsRequested,
    ContentGenerationRequested,
    PromotionOrchestratorRequested,
)


class RenderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PublicationStatus(str, Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class PromotionActionTaken(str, Enum):
    BOOST = "boost"
    FEATURE = "feature"
    CROSS_POST = "cross_post"


class PromotionStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"


class ScheduleMessageType(str, Enum):
    CONTENT_GENERATION = ContentGenerationRequested.topic()
    PROMOTION_ORCHESTRATION = PromotionOrchestratorRequested.topic()
    ANALYTICS_COLLECTION = CollectAnalyticsRequested.topic()
    ACTIVITY_REPORT = ActivityReportRequested.topic()


class TenantUserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class IdentityProvider(str, Enum):
    AZURE_B2C = "azure_b2c"
    GOOGLE = "google"
    GITHUB = "github"
