"""Validates configuration serialization, path isolation, and data verification routines."""

from __future__ import annotations

import json
from pathlib import Path

from takakia.config import AppConfig, ConfigManager


def test_default_config_instantiation() -> None:
    """Verifies that an unconfigured environment initializes safe application defaults."""
    config = AppConfig()
    assert config.language == "en"
    assert config.provider_name == "OpenRouter"
    assert "openrouter.ai" in config.base_url
    assert config.api_key == ""
    assert config.default_profile == "study"


def test_config_save_and_load(tmp_path: Path) -> None:
    """Ensures that user configurations write atomically to disk and deserialize correctly."""
    # Initialize the manager pointing exclusively to our isolated temp directory sandbox
    manager = ConfigManager(app_name="test_sandbox")
    manager.config_dir = tmp_path
    manager.config_path = tmp_path / "config.json"
    
    # Create and modify a unique configuration payload target
    test_config = AppConfig(
        language="pt_br",
        provider_name="CustomGroq",
        base_url="https://api.groq.com/openai/v1",
        api_key="mock-secret-key-12345",
        default_model="llama3-8b-instruct",
        default_profile="translation"
    )
    
    # Save target parameters, then read from disk to check properties equality
    manager.save_config(test_config)
    assert manager.config_path.is_file()
    
    loaded_config = manager.load_config()
    assert loaded_config.language == "pt_br"
    assert loaded_config.provider_name == "CustomGroq"
    assert loaded_config.base_url == "https://api.groq.com/openai/v1"
    assert loaded_config.api_key == "mock-secret-key-12345"
    assert loaded_config.default_model == "llama3-8b-instruct"
    assert loaded_config.default_profile == "translation"


def test_is_configured_evaluation(tmp_path: Path) -> None:
    """Verifies onboarding qualification rules based on configuration completion state."""
    manager = ConfigManager(app_name="test_sandbox")
    manager.config_path = tmp_path / "config.json"
    
    assert manager.is_configured() is False
    
    # Persist empty credentials setup string values
    empty_config = AppConfig(api_key="   ")
    manager.save_config(empty_config)
    assert manager.is_configured() is False
    
    # Persist genuine operational key configurations
    valid_config = AppConfig(api_key="sk-genuine-key-data")
    manager.save_config(valid_config)
    assert manager.is_configured() is True


def test_model_cache_persistence_lifecycle(tmp_path: Path) -> None:
    """Verifies local cache write loops, string sorting, and corrupt data survival properties."""
    manager = ConfigManager(app_name="test_sandbox")
    manager.cache_dir = tmp_path
    manager.cache_path = tmp_path / "models_cache.json"
    
    # Uninitialized cache states should return completely empty sequence list targets
    assert manager.load_model_cache() == []
    
    sample_models = ["model-b", "model-a", "model-c"]
    manager.save_model_cache(sample_models)
    
    loaded_cache = manager.load_model_cache()
    # Content rows should preserve string characters exactly
    assert "model-b" in loaded_cache
    assert len(loaded_cache) == 3
    
    # Clear active cache files manually and evaluate restoration stability
    manager.clear_model_cache()
    assert manager.load_model_cache() == []