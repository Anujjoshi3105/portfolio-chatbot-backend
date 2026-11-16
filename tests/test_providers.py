import pytest
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.providers import get_llm_provider


def test_provider_factory_with_nvidia():
    """Test that the provider factory returns NVIDIA provider when configured."""
    # Set the env var before importing
    os.environ["NVIDIA_API_KEY"] = "sk-test-nvidia-key"
    os.environ["LLM_PROVIDER"] = "nvidia"
    
    # Clear any cached import
    import importlib
    import app.providers
    importlib.reload(app.providers)
    
    provider = get_llm_provider()
    assert provider.__class__.__name__ == "NVIDIAProvider"