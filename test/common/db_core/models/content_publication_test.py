import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import Content, ContentPublication, IntegrationProfile, Project, Tenant, Niche


def test_content_publication_auto_generated_fields(db_session):
    """Test that publication_id and published_at are auto-generated"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest"
    )
    db_session.add(publication)
    db_session.flush()

    assert publication.publication_id is not None
    assert isinstance(publication.publication_id, uuid.UUID)
    assert publication.published_at is not None
    assert isinstance(publication.published_at, datetime)

    db_session.commit()

    assert publication.publication_id is not None
    assert publication.published_at is not None


def test_content_publication_requires_content_id(db_session):
    """Test that content_id is required"""
    publication = ContentPublication(
        channel_key="pinterest"
    )
    publication.content_id = None
    db_session.add(publication)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_content_publication_requires_channel_key(db_session):
    """Test that channel_key is required"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id
    )
    publication.channel_key = None
    db_session.add(publication)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_content_publication_with_invalid_content_id(db_session):
    """Test that creating publication with invalid content_id raises IntegrityError"""
    fake_content_id = uuid.uuid4()

    publication = ContentPublication(
        content_id=fake_content_id,
        channel_key="pinterest"
    )
    db_session.add(publication)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


def test_content_publication_platform_post_id_nullable(db_session):
    """Test that platform_post_id is nullable and defaults to None"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest"
    )
    db_session.add(publication)
    db_session.commit()

    assert publication.platform_post_id is None


def test_content_publication_with_platform_post_id(db_session):
    """Test that platform_post_id can be set"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="1234567890"
    )
    db_session.add(publication)
    db_session.commit()

    assert publication.platform_post_id == "1234567890"


def test_content_publication_platform_metadata_defaults_to_empty(db_session):
    """Test that platform_metadata defaults to empty dict"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest"
    )
    db_session.add(publication)
    db_session.commit()

    assert publication.platform_metadata == {} or publication.platform_metadata is None


def test_content_publication_with_platform_metadata(db_session):
    """Test that platform_metadata can store JSONB data"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    metadata = {
        "board_id": "abc123",
        "section_id": "def456",
        "promoted": True,
        "campaign_id": "campaign_xyz"
    }

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="1234567890",
        platform_metadata=metadata
    )
    db_session.add(publication)
    db_session.commit()

    db_session.expire_all()

    retrieved_pub = db_session.query(ContentPublication).filter_by(
        publication_id=publication.publication_id
    ).first()

    assert retrieved_pub.platform_metadata == metadata
    assert retrieved_pub.platform_metadata["board_id"] == "abc123"
    assert retrieved_pub.platform_metadata["promoted"] is True


def test_content_publication_relationship_to_content(db_session):
    """Test that publication.content relationship works correctly"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    publication = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="1234567890"
    )
    db_session.add(publication)
    db_session.commit()

    db_session.expire_all()

    retrieved_pub = db_session.query(ContentPublication).filter_by(
        publication_id=publication.publication_id
    ).first()

    assert retrieved_pub.content is not None
    assert retrieved_pub.content.content_id == content.content_id
    assert retrieved_pub.content.title == "Test Content"


def test_content_publications_relationship(db_session):
    """Test that content.publications relationship works correctly"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    # Create multiple publications for same content on different channels
    pub1 = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="pin_123"
    )
    pub2 = ContentPublication(
        content_id=content.content_id,
        channel_key="instagram",
        platform_post_id="ig_456"
    )
    pub3 = ContentPublication(
        content_id=content.content_id,
        channel_key="tiktok",
        platform_post_id="tt_789"
    )

    db_session.add_all([pub1, pub2, pub3])
    db_session.commit()

    db_session.expire_all()

    retrieved_content = db_session.query(Content).filter_by(
        content_id=content.content_id
    ).first()

    assert len(retrieved_content.publications) == 3

    channel_keys = [p.channel_key for p in retrieved_content.publications]
    assert "pinterest" in channel_keys
    assert "instagram" in channel_keys
    assert "tiktok" in channel_keys


def test_multiple_publications_same_channel(db_session):
    """Test that same content can be published multiple times to the same channel"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    # Publish to Pinterest twice (e.g., to different boards)
    pub1 = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="pin_123",
        platform_metadata={"board_id": "board_1"}
    )
    pub2 = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest",
        platform_post_id="pin_456",
        platform_metadata={"board_id": "board_2"}
    )

    db_session.add_all([pub1, pub2])
    db_session.commit()

    publications = db_session.query(ContentPublication).filter_by(
        content_id=content.content_id,
        channel_key="pinterest"
    ).all()

    assert len(publications) == 2
    assert publications[0].platform_metadata["board_id"] != publications[1].platform_metadata["board_id"]


def test_cascade_delete_content_deletes_publications(db_session):
    """Test that deleting content cascades to delete publications"""
    content = Content(
        asset_url="https://example.com/image.jpg",
        title="Test Content",
        description="Test description"
    )
    db_session.add(content)
    db_session.commit()

    pub1 = ContentPublication(
        content_id=content.content_id,
        channel_key="pinterest"
    )
    pub2 = ContentPublication(
        content_id=content.content_id,
        channel_key="instagram"
    )
    db_session.add_all([pub1, pub2])
    db_session.commit()

    content_id = content.content_id

    # Delete the content
    db_session.delete(content)
    db_session.commit()

    # Check that publications were also deleted
    publications = db_session.query(ContentPublication).filter_by(
        content_id=content_id
    ).all()

    assert len(publications) == 0


def test_query_publications_by_channel(db_session):
    """Test querying publications filtered by channel_key"""
    content1 = Content(
        asset_url="https://example.com/image1.jpg",
        title="Test Content 1",
        description="Description 1"
    )
    content2 = Content(
        asset_url="https://example.com/image2.jpg",
        title="Test Content 2",
        description="Description 2"
    )
    db_session.add_all([content1, content2])
    db_session.commit()

    # Create publications on different channels
    pinterest_pubs = [
        ContentPublication(content_id=content1.content_id, channel_key="pinterest"),
        ContentPublication(content_id=content2.content_id, channel_key="pinterest"),
    ]
    instagram_pubs = [
        ContentPublication(content_id=content1.content_id, channel_key="instagram"),
    ]

    db_session.add_all(pinterest_pubs + instagram_pubs)
    db_session.commit()

    # Query Pinterest publications
    pinterest_results = db_session.query(ContentPublication).filter_by(
        channel_key="pinterest"
    ).all()
    assert len(pinterest_results) == 2

    # Query Instagram publications
    instagram_results = db_session.query(ContentPublication).filter_by(
        channel_key="instagram"
    ).all()
    assert len(instagram_results) == 1
