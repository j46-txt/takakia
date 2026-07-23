"""
Provider Factory Module.

Centralizes the instantiation logic for various AI provider adapters.
"""

from __future__ import annotations

from takakia.config import ProviderConfig
from takakia.providers.base import BaseProvider
from takakia.providers.compatible import OpenAICompatibleProvider

class ProviderFactory:
    """Factory for generating provider adapters from configuration objects."""

    @staticmethod
    def create(config: ProviderConfig) -> BaseProvider:
        """Instantiates the appropriate provider based on configuration."""
        is_gemini = config.name.lower() in ("gemini", "google") or "generativelanguage.googleapis.com" in config.base_url.lower()

        if is_gemini:
            from takakia.providers.google import GoogleGeminiProvider
            return GoogleGeminiProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                default_model=config.default_model,
                extra_headers=config.extra_headers,
            )
        else:
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                default_model=config.default_model,
                extra_headers=config.extra_headers,
            )