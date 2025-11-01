import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from common.db_core.models import User

def test_user_auto_generated_fields(db_session):
    """Test that user_id and created_at are auto-generated"""
    user = User(
        email="test@example.com",
        provider="google",
        provider_sub="google123"
    )

    db_session.add(user)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert user.user_id is not None
    assert isinstance(user.user_id, uuid.UUID)
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)

    db_session.commit()

    # After commit, values should be maintained
    assert user.user_id is not None
    assert user.created_at is not None


def test_user_required_fields_enforcement(db_session):
    """Test that nullable=False constraints are enforced at DB level"""
    # Missing email
    user = User(provider="google", provider_sub="sub123")
    user.email = None  # Explicitly set to None
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing provider
    user = User(email="test@example.com", provider_sub="sub123")
    user.provider = None
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Missing provider_sub
    user = User(email="test@example.com", provider="google")
    user.provider_sub = None
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


