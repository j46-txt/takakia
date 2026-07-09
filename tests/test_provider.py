"""Mocks transport streams to verify network communication processing and error translations."""

from __future__ import annotations

from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
import httpx

from takakia.providers.base import AuthenticationError, HTTPStatusError, NetworkError
from takakia.providers.compatible import OpenAICompatibleProvider


@pytest.fixture
def mock_provider() -> OpenAICompatibleProvider:
    """Initializes a standard target testing provider adapter configuration."""
    return OpenAICompatibleProvider(
        api_key="mock-test-api-key",
        base_url="https://test.endpoint.gateway/v1",
        default_model="test-stable-llm"
    )


def test_list_models_successful_parsing(mock_provider: OpenAICompatibleProvider) -> None:
    """Ensures successful API payload models map to sorted arrays correctly."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "model-beta"},
            {"id": "model-alpha"}
        ]
    }
    
    with patch("httpx.Client.get", return_value=mock_response):
        models = mock_provider.list_models()
        assert models == ["model-alpha", "model-beta"]


def test_provider_network_timeout_translation(mock_provider: OpenAICompatibleProvider) -> None:
    """Ensures raw transport layer network drops translate into unified internal NetworkErrors."""
    with patch("httpx.Client.get", side_effect=httpx.ConnectTimeout("Connection timed out.")):
        with pytest.raises(NetworkError):
            mock_provider.list_models()


def test_provider_authentication_rejection_translation(mock_provider: OpenAICompatibleProvider) -> None:
    """Validates that 401 Unauthorized API states safely transform into targeted internal AuthenticationErrors."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": {"message": "Invalid API Key token reference details."}}
    
    with patch("httpx.Client.get", return_value=mock_response):
        with pytest.raises(AuthenticationError):
            mock_provider.list_models()


def test_stream_chat_token_extraction(mock_provider: OpenAICompatibleProvider) -> None:
    """Validates SSE protocol line parsing, text fragment handling, and extraction routines."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Simulate realistic line-by-line SSE chunks emitted by LLM endpoints
    mock_response.iter_lines.return_value = [
        "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}",
        "data: ",  
        "data: {\"choices\": [{\"delta\": {\"content\": \" World\"}}]}",
        "data: [DONE]"
    ]
    
    # Mock the internal client stream context manager layout properties
    mock_client = MagicMock()
    # Ensure that calling __enter__ on the Client instance returns our configured mock_client
    mock_client.__enter__.return_value = mock_client
    mock_client.stream.return_value.__enter__.return_value = mock_response
    
    with patch("httpx.Client", return_value=mock_client):
        tokens_iterator = mock_provider.stream_chat(messages=[{"role": "user", "content": "Hi"}])
        tokens_list = list(tokens_iterator)
        
        assert tokens_list == ["Hello", " World"]