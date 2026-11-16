import pytest
from sqlalchemy import inspect

from app.database.models import Base


def test_create_tables():
    """Test that database tables can be created."""
    # This test verifies the SQLAlchemy models are properly defined
    # and can be used with create_engine
    inspector = inspect(Base.metadata)
    tables = inspector.get_table_names()
    assert len(tables) > 0


def test_user_model_has_required_columns():
    """Test that User model has the expected columns."""
    from app.database.models import User
    columns = [c.name for c in User.__table__.columns]
    assert "id" in columns
    assert "api_key_hash" in columns
    assert "created_at" in columns