"""
Universal OpenAI-Compatible API Adapter.

Communicates with any compliant /v1 REST engine endpoint via stateless HTTP protocols,
streaming chunk responses line-by-line while maintaining clean resource closures.
"""

from __future__ import annotations

import json
from typing import Iterator, Optional

import httpx

from takakia.providers.base import (
    AuthenticationError,
    BaseProvider,
    HTTPStatusError,
    NetworkError,
    ProviderError,
)


class OpenAICompatibleProvider(BaseProvider):
    """Universal adapter designed to converse with any OpenAI-v1-compliant service endpoint."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(api_key, base_url, default_model, extra_headers)
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """
        Lazily instantiates and safely recycles a persistent underlying HTTP client pool.
        """
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
            self._client = httpx.Client(timeout=timeout)
        return self._client

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Sends conversation histories to the endpoint and yields text tokens in real time.
        
        Performs proactive chunk assembly and strict type validation to ensure reliability.
        """
        target_model = model.strip() if model else self.default_model
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers
        }
        
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True
        }

        try:
            with self.client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    self._handle_status_error(response)

                for line in response.iter_lines():
                    clean_line = line.strip()
                    if not clean_line or not clean_line.startswith("data:"):
                        continue
                    
                    raw_data = clean_line[5:].strip()
                    if raw_data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(raw_data)
                        if not isinstance(chunk, dict):
                            continue
                            
                        if "error" in chunk:
                            error_obj = chunk["error"]
                            if isinstance(error_obj, dict):
                                error_msg = error_obj.get("message", "An upstream provider error occurred during transmission.")
                            else:
                                error_msg = str(error_obj)
                            raise ProviderError(f"API Streaming Error: {error_msg}")
                            
                        choices = chunk.get("choices", [])
                        if choices and isinstance(choices, list) and len(choices) > 0:
                            choice_entry = choices[0]
                            if isinstance(choice_entry, dict) and "delta" in choice_entry:
                                delta = choice_entry["delta"]
                                if isinstance(delta, dict) and "content" in delta:
                                    content = delta["content"]
                                    if content:
                                        yield str(content)
                    except (json.JSONDecodeError, TypeError, KeyError, IndexError):
                        continue

        except httpx.HTTPError as e:
                    raise NetworkError(f"Network transport infrastructure failure or timeout: {str(e)}", raw_error=e)
        except Exception as e:
            if not isinstance(e, ProviderError):
                raise ProviderError(f"An unexpected internal transport breakdown occurred: {str(e)}", raw_error=e)
            raise

    def list_models(self) -> list[str]:
        """
        Queries the vendor endpoint to discover valid structural AI engine options.
        
        Returns an alphabetically sorted list of alphanumeric model identifiers.
        """
        url = f"{self.base_url}/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers
        }

        try:
            response = self.client.get(url, headers=headers)
            if response.status_code != 200:
                self._handle_status_error(response)
            
            payload = response.json()
            data_list = payload.get("data", [])
            
            models: list[str] = []
            if isinstance(data_list, list):
                for model_obj in data_list:
                    if isinstance(model_obj, dict) and "id" in model_obj:
                        models.append(str(model_obj["id"]))
                        
            return sorted(models)

        except httpx.HTTPError as e:
            raise NetworkError(f"Failed to discover provider models due to a network connection layer error: {str(e)}", raw_error=e)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise ProviderError("The provider server returned a structurally unreadable or malformed JSON payload.", raw_error=e)
        except Exception as e:
            if not isinstance(e, ProviderError):
                raise ProviderError(f"Unexpected operational failure during model mapping exploration: {str(e)}", raw_error=e)
            raise

    def _handle_status_error(self, response: httpx.Response) -> None:
        """Evaluates non-200 HTTP response codes and raises the appropriate provider exception."""
        status = response.status_code
        try:
            response.read()
            err_data = response.json()
            server_msg = err_data.get("error", {}).get("message", response.text)
        except (json.JSONDecodeError, AttributeError, httpx.ResponseNotRead):
            server_msg = response.text or "No contextual server error text supplied."

        if status in (401, 403):
            raise AuthenticationError(f"Credentials rejected by server endpoint. Details: {server_msg}")
        
        raise HTTPStatusError(server_msg, status_code=status)

    def close(self) -> None:
        """Safely tears down lingering connections and associated client transport pools."""
        if self._client is not None and not self._client.is_closed:
            self._client.close()
        self._client = None