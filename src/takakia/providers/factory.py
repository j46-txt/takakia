"""
Provider Factory Module.

Centralizes the instantiation logic for various AI provider adapters.
"""

from __future__ import annotations

from takakia.config import ProviderConfig
from takakia.providers.base import BaseProvider


class ProviderFactory:
    """Factory for generating provider adapters from configuration objects."""

    @staticmethod
    def create(config: ProviderConfig) -> BaseProvider:
        """Instantiates the appropriate provider based on configuration."""
        base_url_lower = config.base_url.lower()
        is_gemini = "generativelanguage.googleapis.com" in base_url_lower

        if is_gemini:
            from takakia.providers.google import GoogleGeminiProvider
            return GoogleGeminiProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                default_model=config.default_model,
                extra_headers=config.extra_headers,
            )
        else:
            from takakia.providers.compatible import OpenAICompatibleProvider
            return OpenAICompatibleProvider(
                api_key=config.api_key,
                base_url=config.base_url,
                default_model=config.default_model,
                extra_headers=config.extra_headers,
            )
