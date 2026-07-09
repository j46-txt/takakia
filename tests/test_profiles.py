"""Verifies dynamic resource lookup operations and package markdown loading mechanisms."""

from __future__ import annotations

from takakia.profiles import ProfileManager


def test_profile_enumeration_discovery() -> None:
    """Ensures profile managers locate and list core structural prompt assets cleanly."""
    manager = ProfileManager()
    available = manager.list_profiles()
    
    assert isinstance(available, list)
    assert "general" in available
    assert "study" in available
    assert "translation" in available


def test_profile_data_loading_and_fallbacks() -> None:
    """Validates markdown resource string retrieval and fallback safety targets."""
    manager = ProfileManager()
    
    study_prompt = manager.load_profile("study")
    assert "tutor" in study_prompt.lower() or "examination" in study_prompt.lower()
    
    # Requesting a non-existent fallback profile should resolve down to general instructions safely
    fallback_prompt = manager.load_profile("completely-fictional-profile-handle")
    assert fallback_prompt is not None
    assert len(fallback_prompt) > 0