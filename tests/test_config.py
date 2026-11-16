import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_config_import():
    """Test that configuration can be imported."""
    import app.core.config as config
    assert config.settings is not None
    assert config.settings.HOST == "0.0.0.0"
    assert config.settings.PORT == 7860

def test_security_import():
    """Test that security utilities can be imported."""
    from app.core.security import hash_api_key, verify_api_key
    hashed = hash_api_key("test-key")
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 produces 64 hex chars
    assert verify_api_key("test-key", hashed) == True