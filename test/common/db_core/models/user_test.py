from common.db_core.models import User

def test_basic_creation():
    """Test basic User object creation"""
    user = User(
        email = "testemail@email.com"
        , provider = "testprovider"
        , provider_sub = "testprovidersub"
    )

    assert user.email == "testemail@email.com"


def test_user_persistence(db_session):
    """Test saving and retrieving from database"""
    user = User(
        email = "testemail@email.com"
        , provider = "testprovider"
        , provider_sub = "testprovidersub"
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter_by(email="testemail@email.com").first()
    assert retrieved is not None
    assert retrieved.user_id == user.user_id