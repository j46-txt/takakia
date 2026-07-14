"""
Native Google Gemini API Provider Adapter.

Communicates with the official Gemini REST endpoints via raw HTTPX streaming protocol structures,
avoiding heavy external SDK dependencies while maintaining type fidelity.
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


class GoogleGeminiProvider(BaseProvider):
    """Concrete provider adapter engineered to converse natively with the Google Gemini REST API."""

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
        Sends conversation sequences to Gemini's native streaming endpoint and yields text tokens.
        """
        target_model = model.strip() if model else self.default_model
        model_name = target_model
        if model_name.startswith("models/"):
            model_name = model_name[7:]

        # Formulate native Gemini REST URI with explicit SSE transport mapping
        url = f"{self.base_url}/v1beta/models/{model_name}:streamGenerateContent"
        params = {"alt": "sse", "key": self.api_key}
        
        headers = {
            "Content-Type": "application/json",
            **self.extra_headers
        }

        # Transpose standardized frame history arrays into Gemini's contents layout matrix
        contents = []
        system_instruction_text = ""

        for msg in messages:
            role = msg.get("role", "user").lower().strip()
            content = msg.get("content", "").strip()
            
            if role == "system":
                system_instruction_text = content
                continue
                
            gemini_role = "user" if role == "user" else "model"
            
            # Prevent HTTP 400 by folding consecutive identical roles
            if contents and contents[-1]["role"] == gemini_role:
                contents[-1]["parts"][0]["text"] += f"\n\n{content}"
            else:
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        payload = {
            "contents": contents
        }
        
        if system_instruction_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction_text}]
            }

        try:
            event_buffer = []
            with self.client.stream("POST", url, headers=headers, params=params, json=payload) as response:
                if response.status_code != 200:
                    self._handle_status_error(response)

                for line in response.iter_lines():
                    # An empty line denotes the end of an SSE event block
                    if not line:
                        if not event_buffer:
                            continue
                            
                        # Reconstruct multi-line JSON structures natively compliant with SSE
                        raw_data = "\n".join(event_buffer)
                        event_buffer.clear()
                        
                        if raw_data.strip() == "[DONE]":
                            break
                            
                        try:
                            chunk = json.loads(raw_data)
                            if not isinstance(chunk, dict):
                                continue
                                
                            if "error" in chunk:
                                error_obj = chunk["error"]
                                if isinstance(error_obj, dict):
                                    error_msg = error_obj.get("message", "An upstream Gemini provider error occurred.")
                                else:
                                    error_msg = str(error_obj)
                                raise ProviderError(f"API Streaming Error: {error_msg}")
                                
                            candidates = chunk.get("candidates", [])
                            if candidates and isinstance(candidates, list) and len(candidates) > 0:
                                candidate = candidates[0]
                                if isinstance(candidate, dict) and "content" in candidate:
                                    content_obj = candidate["content"]
                                    if isinstance(content_obj, dict) and "parts" in content_obj:
                                        parts = content_obj["parts"]
                                        if isinstance(parts, list):
                                            for part in parts:
                                                if isinstance(part, dict) and "text" in part:
                                                    text = part["text"]
                                                    if text:
                                                        yield str(text)
                        except (json.JSONDecodeError, TypeError, KeyError, IndexError):
                            continue
                    
                    # Accumulate data lines for the current event
                    elif line.startswith("data:"):
                        # Extract the payload safely
                        event_buffer.append(line[5:].removeprefix(" "))

        except httpx.HTTPError as e:
            raise NetworkError(f"Network transport infrastructure failure or timeout: {str(e)}", raw_error=e)
        except Exception as e:
            if not isinstance(e, ProviderError):
                raise ProviderError(f"An unexpected internal transport breakdown occurred: {str(e)}", raw_error=e)
            raise

    def list_models(self) -> list[str]:
        """
        Queries the Gemini vendor endpoint to discover valid structural AI engine options.
        """
        url = f"{self.base_url}/v1beta/models"
        params = {"key": self.api_key}
        headers = {
            "Content-Type": "application/json",
            **self.extra_headers
        }

        try:
            response = self.client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                self._handle_status_error(response)
            
            payload = response.json()
            models_list = payload.get("models", [])
            
            models: list[str] = []
            if isinstance(models_list, list):
                for m in models_list:
                    if isinstance(m, dict) and "name" in m:
                        name = str(m["name"])
                        if name.startswith("models/"):
                            name = name[7:]
                            
                        supported_actions = m.get("supportedActions", [])
                        if "generateContent" in supported_actions or name.startswith("gemini"):
                            models.append(name)
                        
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
