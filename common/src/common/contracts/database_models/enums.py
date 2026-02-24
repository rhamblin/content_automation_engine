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


class PublicationActionTaken(str, Enum):
    NONE = "none"
    UPDATE = "update"
    DELETE = "delete"
    ADD_TO_CAMPAIGN = "add_to_campaign"


class PromotionActionTaken(str, Enum):
    NONE = "none"
    ADJUST = "adjust"
    PAUSE = "pause"
    REMOVE = "remove"


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


class KeywordIntent(str, Enum):
    INFORMATIONAL = "informational"
    BUYER = "buyer"
    BUYER_INFO = "buyer_info"


class IdentityProvider(str, Enum):
    AZURE_B2C = "azure_b2c"
    AZURE_ENTRA = "azure_entra"
    GOOGLE = "google"
    GITHUB = "github"
