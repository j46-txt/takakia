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
class AppConfig:
    """Data structure representing the application user configuration settings."""

    language: str = "en"
    provider_name: str = "OpenRouter"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    default_model: str = "meta-llama/llama-3.1-8b-instruct"
    default_profile: str = "default"
    extra_headers: dict[str, str] = field(default_factory=dict)


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
        """Guarantees that all platform-compliant application paths exist securely."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        """
        Loads the runtime application configuration from disk.
        
        Returns a default AppConfig instance if the file does not exist or
        is corrupted. Safely validates incoming dictionary types to protect
        against configuration poisoning anomalies.
        """
        if not self.config_path.is_file():
            return AppConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return AppConfig()
                
            valid_keys = {f.name for f in fields(AppConfig)}
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            
            # Enforce strong type bounds before initializing the runtime state
            config = AppConfig()
            if "language" in filtered_data and isinstance(filtered_data["language"], str):
                config.language = filtered_data["language"]
            if "provider_name" in filtered_data and isinstance(filtered_data["provider_name"], str):
                config.provider_name = filtered_data["provider_name"]
            if "base_url" in filtered_data and isinstance(filtered_data["base_url"], str):
                config.base_url = filtered_data["base_url"]
            if "api_key" in filtered_data and isinstance(filtered_data["api_key"], str):
                config.api_key = filtered_data["api_key"]
            if "default_model" in filtered_data and isinstance(filtered_data["default_model"], str):
                config.default_model = filtered_data["default_model"]
            if "default_profile" in filtered_data and isinstance(filtered_data["default_profile"], str):
                config.default_profile = filtered_data["default_profile"]
            if "extra_headers" in filtered_data and isinstance(filtered_data["extra_headers"], dict):
                config.extra_headers = {str(k): str(v) for k, v in filtered_data["extra_headers"].items()}
                
            return config
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError, OSError):
            return AppConfig()

    def save_config(self, config: AppConfig) -> None:
        """
        Persists the application configuration securely to disk.
        
        Enforces strict file permissions from the moment of creation via low-level
        descriptors on POSIX filesystems to guarantee secret tokens are never exposed.
        Contains a robust retry loop to handle transient Windows filesystem locks.
        """
        self.ensure_directories()
        temp_path = self.config_path.with_suffix(".tmp")
        
        try:
            if os.name == "posix":
                if temp_path.exists():
                    temp_path.unlink()
                # Create the file with strict permissions securely up front
                fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                os.close(fd)  # Relinquish low level descriptor safely immediately
                
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(asdict(config), f, indent=4, ensure_ascii=False)
            else:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(asdict(config), f, indent=4, ensure_ascii=False)
                    
            # Resilient atomic swap mechanism with retry fallback for process locks
            retries = 3
            for attempt in range(retries):
                try:
                    temp_path.replace(self.config_path)
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

    def is_configured(self) -> bool:
        """Evaluates whether the application contains an initial core API credential setup."""
        if not self.config_path.is_file():
            return False
        config = self.load_config()
        return bool(config.api_key and config.api_key.strip())

    def load_model_cache(self) -> list[str]:
        """
        Retrieves the cached collection of vendor models discovered from prior cycles.
        
        Returns an empty list if the cache is absent or structurally unreadable.
        """
        if not self.cache_path.is_file():
            return []

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "models" in data and isinstance(data["models"], list):
                    return [str(m) for m in data["models"] if m]
            return []
        except (json.JSONDecodeError, TypeError, OSError):
            return []

    def save_model_cache(self, models: list[str]) -> None:
        """Stores structural model lists derived dynamically during discovery routines."""
        self.ensure_directories()
        cache_data = {"models": models}
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
        """Wipes persistent local model lists forcing network discovery on next request."""
        try:
            self.cache_path.unlink(missing_ok=True)
        except OSError:
            pass
