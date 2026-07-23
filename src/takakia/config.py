"""
Configuration and Cache Management System.

Handles platform-compliant directory discovery, configuration file persistence,
model discovery caching, and file-system security.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import platformdirs

APP_NAME = "takakia"

@dataclass
class ProviderConfig:
    """Data structure representing a specific provider's credentials and settings."""
    name: str = "OpenRouter"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    default_model: str = "meta-llama/llama-3.1-8b-instruct"
    extra_headers: dict[str, str] = field(default_factory=dict)

@dataclass
class AppConfig:
    """Data structure representing the application user configuration settings."""

    language: str = "en"
    default_profile: str = "default"
    active_provider: str = "openrouter"
    providers: dict[str, ProviderConfig] = field(default_factory=lambda: {
        "openrouter": ProviderConfig(name="OpenRouter")
    })

    @property
    def active_provider_config(self) -> ProviderConfig:
        """Safely resolves the currently active provider configuration."""
        if self.active_provider not in self.providers:
            if self.providers:
                self.active_provider = next(iter(self.providers))
            else:
                self.providers["openrouter"] = ProviderConfig()
                self.active_provider = "openrouter"
        return self.providers[self.active_provider]

    # Backward compatibility proxies delegating to the active provider
    @property
    def provider_name(self) -> str:
        return self.active_provider_config.name

    @provider_name.setter
    def provider_name(self, value: str) -> None:
        self.active_provider_config.name = value

    @property
    def base_url(self) -> str:
        return self.active_provider_config.base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        self.active_provider_config.base_url = value

    @property
    def api_key(self) -> str:
        return self.active_provider_config.api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        self.active_provider_config.api_key = value

    @property
    def default_model(self) -> str:
        return self.active_provider_config.default_model

    @default_model.setter
    def default_model(self, value: str) -> None:
        self.active_provider_config.default_model = value

    @property
    def extra_headers(self) -> dict[str, str]:
        return self.active_provider_config.extra_headers

    @extra_headers.setter
    def extra_headers(self, value: dict[str, str]) -> None:
        self.active_provider_config.extra_headers = value

    @property
    def is_gemini_native(self) -> bool:
        return self.provider_name.lower() in ("gemini", "google") or "generativelanguage.googleapis.com" in self.base_url.lower()

class ConfigManager:
    """Manages serialization, retrieval, and runtime updating of application states."""

    def __init__(self, app_name: str = APP_NAME) -> None:
        self.app_name = app_name
        self.config_dir = Path(platformdirs.user_config_dir(self.app_name))
        self.cache_dir = Path(platformdirs.user_cache_dir(self.app_name))
        self.log_dir = Path(platformdirs.user_log_dir(self.app_name))
        
        self.config_path = self.config_dir / "config.json"
        self.cache_path = self.cache_dir / "models_cache.json"

    def ensure_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        if not self.config_path.is_file():
            return AppConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return AppConfig()
                
            config = AppConfig()
            
            if "language" in data and isinstance(data["language"], str):
                config.language = data["language"]
            if "default_profile" in data and isinstance(data["default_profile"], str):
                config.default_profile = data["default_profile"]
                
            if "providers" in data and isinstance(data["providers"], dict):
                config.providers = {}
                for k, v in data["providers"].items():
                    if isinstance(v, dict):
                        config.providers[k] = ProviderConfig(
                            name=v.get("name", k),
                            base_url=v.get("base_url", ""),
                            api_key=v.get("api_key", ""),
                            default_model=v.get("default_model", ""),
                            extra_headers=v.get("extra_headers", {})
                        )
                if "active_provider" in data and isinstance(data["active_provider"], str):
                    config.active_provider = data["active_provider"]
            else:
                # Automatic Migration of Legacy Configs
                p_name = data.get("provider_name", "openrouter")
                key_name = p_name.lower().replace(" ", "_")
                config.providers = {
                    key_name: ProviderConfig(
                        name=p_name,
                        base_url=data.get("base_url", "https://openrouter.ai/api/v1"),
                        api_key=data.get("api_key", ""),
                        default_model=data.get("default_model", "meta-llama/llama-3.1-8b-instruct"),
                        extra_headers=data.get("extra_headers", {})
                    )
                }
                config.active_provider = key_name
                self.save_config(config) # Persist migrated structure
                
            return config
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError, OSError):
            return AppConfig()

    def save_config(self, config: AppConfig) -> None:
        self.ensure_directories()
        temp_path = self.config_path.with_suffix(".tmp")
        fd = None
        
        config_dict = {
            "language": config.language,
            "default_profile": config.default_profile,
            "active_provider": config.active_provider,
            "providers": {k: asdict(v) for k, v in config.providers.items()}
        }
        
        try:
            if os.name == "posix":
                if temp_path.exists():
                    temp_path.unlink()
                fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    fd = None 
                    json.dump(config_dict, f, indent=4, ensure_ascii=False)
            else:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(config_dict, f, indent=4, ensure_ascii=False)
                    
            retries = 3
            for attempt in range(retries):
                try:
                    temp_path.replace(self.config_path)
                    break
                except (OSError, PermissionError, FileExistsError):
                    if attempt == retries - 1:
                        raise
                    time.sleep(0.1)
        except BaseException:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            raise

    def is_configured(self) -> bool:
        if not self.config_path.is_file():
            return False
        config = self.load_config()
        return bool(config.api_key and config.api_key.strip())

    def load_model_cache(self, provider_key: str = None) -> list[str]:
        if not self.cache_path.is_file():
            return []

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                return []
                
            if "providers" in data:
                if provider_key and provider_key in data["providers"]:
                    return [str(m) for m in data["providers"][provider_key] if m]
                return []
            elif "models" in data:
                # Legacy compatibility fallback
                return [str(m) for m in data["models"] if m]
            
            return []
        except (json.JSONDecodeError, TypeError, OSError):
            return []

    def save_model_cache(self, models: list[str], provider_key: str = None) -> None:
        self.ensure_directories()
        
        cache_data = {"providers": {}}
        if self.cache_path.is_file():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    if "providers" in old_data:
                        cache_data = old_data
                    elif "models" in old_data and provider_key:
                        cache_data["providers"][provider_key] = old_data["models"]
            except (json.JSONDecodeError, OSError):
                pass
        
        if provider_key:
            cache_data["providers"][provider_key] = models
            
        temp_path = self.cache_path.with_suffix(".tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4, ensure_ascii=False)
                
            retries = 3
            for attempt in range(retries):
                try:
                    temp_path.replace(self.cache_path)
                    break
                except (OSError, PermissionError, FileExistsError):
                    if attempt == retries - 1:
                        raise
                    time.sleep(0.1)
        except Exception:
            if temp_path.is_file():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def clear_model_cache(self) -> None:
        try:
            self.cache_path.unlink(missing_ok=True)
        except OSError:
            pass
