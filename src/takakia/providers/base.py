"""
Abstract Provider Interface and Common Exceptions.

Defines the structural blueprint and error-handling landscape for all AI model
communication clients.
"""

from __future__ import annotations

import abc
from typing import Any, Iterator, Optional


class ProviderError(Exception):
    """Base exception for all errors encountered during provider interactions."""
    
    def __init__(self, message: str, raw_error: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.raw_error = raw_error


class AuthenticationError(ProviderError):
    """Raised when an API key is rejected or missing entirely from requests."""
    pass


class NetworkError(ProviderError):
    """Raised when communication routes time out or connectivity drops entirely."""
    pass


class HTTPStatusError(ProviderError):
    """Raised when the remote server handles the request but returns an error status code."""
    
    def __init__(self, message: str, status_code: int, raw_error: Optional[Exception] = None) -> None:
        super().__init__(f"HTTP {status_code}: {message}", raw_error=raw_error)
        self.status_code = status_code


class BaseProvider(abc.ABC):
    """
    Abstract Base Class acting as the unified gateway for all AI interactions.
    
    All concrete API adapter wrappers must inherit from this class and
    fulfill its structural definitions.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.default_model = default_model.strip()
        self.extra_headers = extra_headers or {}

    @abc.abstractmethod
    def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Sends a conversation sequence history block to the provider and streams tokens.
        
        Args:
            messages: A list of structural conversation frames. 
                      Example: [{"role": "user", "content": "Hello"}]
            model: An optional override target model identifier string. If not provided,
                   utilizes the instance default_model configuration state.
                   
        Yields:
            Textual string tokens as they are produced in real-time by the vendor endpoint.
            
        Raises:
            ProviderError: Or its relevant subclass variants upon execution failure.
        """
        pass

    @abc.abstractmethod
    def list_models(self) -> list[str]:
        """
        Queries the provider endpoint to discover available AI engine model tokens.
        
        Returns:
            A list of valid string model identifiers discovered from the vendor,
            sorted alphabetically.
            
        Raises:
            ProviderError: Or its relevant subclass variants upon execution failure.
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """
        Safely tears down lingering connections and associated client transport pools.
        """
        pass