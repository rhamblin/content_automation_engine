import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from common.db_core.models import Keyword, Niche


# ============================================================================
# Group 1: Auto-Generated Fields
# ============================================================================

def test_keyword_auto_generated_fields(db_session):
    """Test that keyword_id is auto-generated"""
    # Create niche dependency
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create keyword
    keyword = Keyword(niche_id=niche.niche_id, name="artificial intelligence")

    db_session.add(keyword)
    db_session.flush()  # Trigger default value generation

    # After flush (before commit), defaults should be set
    assert keyword.keyword_id is not None
    assert isinstance(keyword.keyword_id, uuid.UUID)

    db_session.commit()

    # After commit, values should be maintained
    assert keyword.keyword_id is not None


# ============================================================================
# Group 2: Required Field Constraints
# ============================================================================

def test_keyword_requires_niche_id(db_session):
    """Test that niche_id is required (nullable=False constraint)"""
    # Create niche dependency
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Try to create Keyword with niche_id = None
    keyword = Keyword(name="machine learning")
    keyword.niche_id = None  # Explicitly set to None
    db_session.add(keyword)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_keyword_requires_keyword_text(db_session):
    """Test that keyword text is required (nullable=False constraint)"""
    # Create niche dependency
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Try to create Keyword with keyword = None
    keyword = Keyword(niche_id=niche.niche_id)
    keyword.name = None  # Explicitly set to None
    db_session.add(keyword)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ============================================================================
# Group 3: Foreign Key Enforcement
# ============================================================================

def test_keyword_requires_valid_niche_fk(db_session):
    """Test that keyword must reference an existing niche (FK constraint)"""
    # Try to create Keyword with fake niche_id
    fake_niche_id = uuid.uuid4()
    keyword = Keyword(niche_id=fake_niche_id, name="invalid keyword")
    db_session.add(keyword)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    # Verify it's a FK constraint violation
    assert "foreign key constraint" in str(exc_info.value).lower()
    db_session.rollback()


# ============================================================================
# Group 4: Relationship Loading
# ============================================================================

def test_keyword_niche_relationship(db_session):
    """Test that keyword.niche relationship works correctly"""
    # Create niche
    niche = Niche(name="Technology", domain="tech.com", default_budget=2000)
    db_session.add(niche)
    db_session.commit()

    # Create keyword
    keyword = Keyword(niche_id=niche.niche_id, name="cloud computing")
    db_session.add(keyword)
    db_session.commit()

    # Clear session to test lazy loading
    db_session.expire_all()

    # Retrieve keyword and verify niche relationship loaded
    retrieved_keyword = db_session.query(Keyword).filter_by(
        keyword_id=keyword.keyword_id
    ).first()

    assert retrieved_keyword.niche is not None
    assert retrieved_keyword.niche.niche_id == niche.niche_id
    assert retrieved_keyword.niche.name == "Technology"
    assert retrieved_keyword.niche.domain == "tech.com"


# ============================================================================
# Group 5: Cascade Delete Behavior
# ============================================================================

def test_delete_niche_cascades_to_keywords(db_session):
    """Test that deleting niche cascades to delete keywords (ON DELETE CASCADE)"""
    # Create niche
    niche = Niche(name="Health & Fitness", domain="health.com", default_budget=1500)
    db_session.add(niche)
    db_session.commit()

    # Create multiple keywords for the niche
    keyword1 = Keyword(niche_id=niche.niche_id, name="yoga")
    keyword2 = Keyword(niche_id=niche.niche_id, name="meditation")
    keyword3 = Keyword(niche_id=niche.niche_id, name="nutrition")
    db_session.add_all([keyword1, keyword2, keyword3])
    db_session.commit()

    # Verify keywords exist
    assert db_session.query(Keyword).filter_by(niche_id=niche.niche_id).count() == 3

    # Store keyword IDs for verification
    keyword_ids = [keyword1.keyword_id, keyword2.keyword_id, keyword3.keyword_id]

    # Delete niche
    db_session.delete(niche)
    db_session.commit()

    # Verify cascade delete worked - keywords should be deleted
    assert db_session.query(Keyword).filter_by(niche_id=niche.niche_id).count() == 0
    for keyword_id in keyword_ids:
        assert db_session.query(Keyword).filter_by(keyword_id=keyword_id).first() is None


# ============================================================================
# Group 6: Multiple Keywords Per Niche
# ============================================================================

def test_multiple_keywords_per_niche(db_session):
    """Test that one niche can have multiple keywords"""
    # Create niche
    niche = Niche(name="Finance", domain="finance.com", default_budget=3000)
    db_session.add(niche)
    db_session.commit()

    # Create multiple keywords for the same niche
    keywords_text = [
        "cryptocurrency",
        "stocks",
        "investing",
        "trading",
        "portfolio management"
    ]

    keywords = []
    for kw_text in keywords_text:
        keyword = Keyword(niche_id=niche.niche_id, name=kw_text)
        keywords.append(keyword)

    db_session.add_all(keywords)
    db_session.commit()

    # Verify all keywords belong to same niche
    retrieved_keywords = db_session.query(Keyword).filter_by(niche_id=niche.niche_id).all()
    assert len(retrieved_keywords) == 5

    retrieved_keywords_text = {kw.name for kw in retrieved_keywords}
    assert retrieved_keywords_text == set(keywords_text)

    # Verify niche can access all keywords via relationship
    db_session.expire_all()
    retrieved_niche = db_session.query(Niche).filter_by(name="Finance").first()
    assert len(retrieved_niche.keywords) == 5
    niche_keywords_text = {kw.name for kw in retrieved_niche.keywords}
    assert niche_keywords_text == set(keywords_text)


# ============================================================================
# Group 7: Method Testing
# ============================================================================

def test_keyword_to_dict(db_session):
    """Test that to_dict() returns correct structure"""
    # Create niche
    niche = Niche(name="Travel", domain="travel.com", default_budget=1200)
    db_session.add(niche)
    db_session.commit()

    # Create keyword
    keyword = Keyword(niche_id=niche.niche_id, name="backpacking")
    db_session.add(keyword)
    db_session.commit()

    # Test to_dict()
    keyword_dict = keyword.to_dict()

    assert isinstance(keyword_dict, dict)
    assert "keyword_id" in keyword_dict
    assert "niche_id" in keyword_dict
    assert "name" in keyword_dict

    # Verify UUIDs are converted to strings
    assert keyword_dict["keyword_id"] == str(keyword.keyword_id)
    assert keyword_dict["niche_id"] == str(niche.niche_id)
    assert keyword_dict["name"] == "backpacking"

    # Verify it's a proper UUID string
    uuid.UUID(keyword_dict["keyword_id"])
    uuid.UUID(keyword_dict["niche_id"])


def test_keyword_to_readable_with_loaded_niche(db_session):
    """Test to_readable() when niche relationship is loaded"""
    # Create niche
    niche = Niche(name="Food & Cooking", domain="food.com", default_budget=1800)
    db_session.add(niche)
    db_session.commit()

    # Create keyword
    keyword = Keyword(niche_id=niche.niche_id, name="vegan recipes")
    db_session.add(keyword)
    db_session.commit()

    # Niche relationship should be loaded due to lazy="selectin"
    readable = keyword.to_readable()

    assert isinstance(readable, str)
    assert "Keyword[" in readable
    assert str(keyword.keyword_id) in readable
    assert "'vegan recipes'" in readable
    assert "niche='Food & Cooking'" in readable
    assert f"niche_id={niche.niche_id}" in readable


def test_keyword_to_readable_without_loaded_niche(db_session):
    """Test to_readable() handles gracefully when niche is not loaded"""
    # Create niche
    niche = Niche(name="Sports", domain="sports.com", default_budget=2500)
    db_session.add(niche)
    db_session.commit()

    # Create keyword
    keyword = Keyword(niche_id=niche.niche_id, name="basketball")
    db_session.add(keyword)
    db_session.commit()

    # Create a detached instance without niche loaded
    keyword_id = keyword.keyword_id
    niche_id = keyword.niche_id
    db_session.expunge(keyword)  # Detach from session

    # Create new keyword instance without loading niche
    detached_keyword = Keyword(keyword_id=keyword_id, niche_id=niche_id, name="basketball")
    detached_keyword.niche = None  # Explicitly set niche to None

    readable = detached_keyword.to_readable()

    # Should handle gracefully without niche name
    assert isinstance(readable, str)
    assert "Keyword[" in readable
    assert str(keyword_id) in readable
    assert "'basketball'" in readable
    assert f"niche_id={niche_id}" in readable


# ============================================================================
# Group 8: Edge Cases & Data Validation
# ============================================================================

def test_keyword_empty_string(db_session):
    """Test keyword with empty string should be rejected"""
    # Create niche
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Try to create keyword with empty string
    keyword = Keyword(niche_id=niche.niche_id, name="")
    db_session.add(keyword)

    # Should raise IntegrityError due to check constraint
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert "ck_keyword_not_empty" in str(exc_info.value).lower()
    db_session.rollback()


def test_keyword_very_long_text(db_session):
    """Test keyword with very long text"""
    # Create niche
    niche = Niche(name="Test Niche", domain="test.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Create keyword with very long text (500 characters)
    long_keyword = "a" * 500
    keyword = Keyword(niche_id=niche.niche_id, name=long_keyword)
    db_session.add(keyword)
    db_session.commit()

    # Should be stored and retrieved correctly
    retrieved = db_session.query(Keyword).filter_by(keyword_id=keyword.keyword_id).first()
    assert retrieved.name == long_keyword
    assert len(retrieved.name) == 500

def test_keyword_special_characters(db_session):
    """Test keywords with special characters and unicode"""
    # Create niche
    niche = Niche(name="International", domain="international.com", default_budget=1000)
    db_session.add(niche)
    db_session.commit()

    # Test various special characters
    special_keywords = [
        "AI & ML",
        "C++",
        "data-science",
        "blockchain/crypto",
        "café ☕",
        "日本語",
        "emoji 🚀🌟",
        "quote's apostrophe",
        'double"quotes',
        "special@#$%^&*()"
    ]

    keywords = []
    for kw_text in special_keywords:
        keyword = Keyword(niche_id=niche.niche_id, name=kw_text)
        keywords.append(keyword)

    db_session.add_all(keywords)
    db_session.commit()

    # Verify all were stored correctly
    retrieved = db_session.query(Keyword).filter_by(niche_id=niche.niche_id).all()
    assert len(retrieved) == len(special_keywords)

    retrieved_text = {kw.name for kw in retrieved}
    assert retrieved_text == set(special_keywords)

def test_duplicate_keywords_in_same_niche(db_session):
    """Test that duplicate keyword text is NOT allowed in the same niche"""
    # Create niche
    niche = Niche(name="Marketing", domain="marketing.com", default_budget=1500)
    db_session.add(niche)
    db_session.commit()

    # Store niche_id before any potential rollback
    niche_id = niche.niche_id

    # Create first keyword
    keyword1 = Keyword(niche_id=niche_id, name="SEO")
    db_session.add(keyword1)
    db_session.commit()

    # Try to create duplicate keyword (same text, same niche)
    keyword2 = Keyword(niche_id=niche_id, name="SEO")
    db_session.add(keyword2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert "uq_keyword_per_niche" in str(exc_info.value).lower()
    db_session.rollback()

def test_duplicate_keywords_across_niches(db_session):
    """Test that same keyword text can exist across different niches"""
    # Create two different niches
    niche1 = Niche(name="Tech", domain="tech.com", default_budget=1000)
    niche2 = Niche(name="Business", domain="business.com", default_budget=2000)
    db_session.add_all([niche1, niche2])
    db_session.commit()

    # Create same keyword text for different niches
    keyword1 = Keyword(niche_id=niche1.niche_id, name="automation")
    keyword2 = Keyword(niche_id=niche2.niche_id, name="automation")
    db_session.add_all([keyword1, keyword2])
    db_session.commit()

    # Should be allowed
    all_automation = db_session.query(Keyword).filter_by(name="automation").all()
    assert len(all_automation) == 2
    assert keyword1.niche_id != keyword2.niche_id


# ============================================================================
# Group 9: CRUD Operations
# ============================================================================

def test_keyword_create_read_update_delete(db_session):
    """Test basic CRUD lifecycle for keyword"""
    # Create niche
    niche = Niche(name="Education", domain="education.com", default_budget=1100)
    db_session.add(niche)
    db_session.commit()

    # CREATE
    keyword = Keyword(niche_id=niche.niche_id, name="online learning")
    db_session.add(keyword)
    db_session.commit()
    keyword_id = keyword.keyword_id

    # READ
    retrieved = db_session.query(Keyword).filter_by(keyword_id=keyword_id).first()
    assert retrieved is not None
    assert retrieved.name == "online learning"
    assert retrieved.niche_id == niche.niche_id

    # UPDATE
    retrieved.name = "e-learning platforms"
    db_session.commit()

    updated = db_session.query(Keyword).filter_by(keyword_id=keyword_id).first()
    assert updated.name == "e-learning platforms"

    # DELETE
    db_session.delete(updated)
    db_session.commit()

    deleted = db_session.query(Keyword).filter_by(keyword_id=keyword_id).first()
    assert deleted is None


# ============================================================================
# Group 10: Orphaned Keywords
# ============================================================================

def test_no_orphaned_keywords_after_niche_deletion(db_session):
    """Test that keywords don't become orphaned when their parent niche is deleted"""
    # Create niche with keywords
    niche = Niche(name="Gaming", domain="gaming.com", default_budget=2200)
    db_session.add(niche)
    db_session.commit()

    # Create keywords
    keyword1 = Keyword(niche_id=niche.niche_id, name="esports")
    keyword2 = Keyword(niche_id=niche.niche_id, name="streaming")
    keyword3 = Keyword(niche_id=niche.niche_id, name="multiplayer")
    db_session.add_all([keyword1, keyword2, keyword3])
    db_session.commit()

    keyword_ids = [keyword1.keyword_id, keyword2.keyword_id, keyword3.keyword_id]
    niche_id = niche.niche_id

    # Verify keywords exist before deletion
    assert db_session.query(Keyword).filter_by(niche_id=niche_id).count() == 3

    # Delete niche
    db_session.delete(niche)
    db_session.commit()

    # Verify no orphaned keywords exist
    orphaned_keywords = db_session.query(Keyword).filter(
        Keyword.keyword_id.in_(keyword_ids)
    ).all()
    assert len(orphaned_keywords) == 0

    # Also verify by niche_id
    keywords_by_niche = db_session.query(Keyword).filter_by(niche_id=niche_id).all()
    assert len(keywords_by_niche) == 0


def test_keyword_query_by_niche_after_multiple_operations(db_session):
    """Test querying keywords by niche after multiple create/delete operations"""
    # Create niche
    niche = Niche(name="Photography", domain="photo.com", default_budget=1600)
    db_session.add(niche)
    db_session.commit()

    # Add initial keywords
    kw1 = Keyword(niche_id=niche.niche_id, name="portrait")
    kw2 = Keyword(niche_id=niche.niche_id, name="landscape")
    kw3 = Keyword(niche_id=niche.niche_id, name="macro")
    db_session.add_all([kw1, kw2, kw3])
    db_session.commit()

    # Verify count
    assert db_session.query(Keyword).filter_by(niche_id=niche.niche_id).count() == 3

    # Delete one keyword
    db_session.delete(kw2)
    db_session.commit()

    # Add new keyword
    kw4 = Keyword(niche_id=niche.niche_id, name="street photography")
    db_session.add(kw4)
    db_session.commit()

    # Final count should be 3 (added 3, deleted 1, added 1)
    final_keywords = db_session.query(Keyword).filter_by(niche_id=niche.niche_id).all()
    assert len(final_keywords) == 3

    final_keywords_text = {kw.name for kw in final_keywords}
    assert final_keywords_text == {"portrait", "macro", "street photography"}
    assert "landscape" not in final_keywords_text
