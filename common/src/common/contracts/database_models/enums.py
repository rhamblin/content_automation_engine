from enum import Enum


class ImageKind(str, Enum):
    ORIGINAL = "original"
    STYLED = "styled"
    THUMBNAIL = "thumbnail"


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
    CONTENT_GENERATION = "content_generation"
    PUBLICATION = "publication"
    ANALYTICS_COLLECTION = "analytics_collection"
    PROMOTION = "promotion"


class TenantUserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class IdentityProvider(str, Enum):
    AZURE_B2C = "azure_b2c"
    GOOGLE = "google"
    GITHUB = "github"
