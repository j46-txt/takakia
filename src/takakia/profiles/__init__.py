"""
Dynamic System Prompt Profile Subsystem.

Loads, caches, and enumerates system prompt instructions from embedded package markdown
resources as well as external user-defined configuration directories.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path
import platformdirs


class ProfileManager:
    """Discovers and retrieves Markdown system prompt profiles stored within the application."""

    def __init__(self) -> None:
        self._package_anchor = "takakia.profiles"
        # Establish a dynamic pathway to the user's local configuration directory
        self.user_profiles_dir = Path(platformdirs.user_config_dir("takakia")) / "profiles"

    def list_profiles(self) -> list[str]:
        """
        Dynamically enumerates all available prompt profile names.

        Scans both the local user configuration profiles directory and the embedded
        package resource directory for markdown files, returning their base names
        sorted alphabetically.
        """
        profiles: set[str] = {"disabled"}

        # 1. Scan external user configuration directory if it exists
        try:
            if self.user_profiles_dir.exists() and self.user_profiles_dir.is_dir():
                for item in self.user_profiles_dir.iterdir():
                    if item.is_file() and item.name.endswith(".md"):
                        profiles.add(item.name[:-3].lower())
        except OSError:
            pass

        # 2. Scan internal embedded package resources
        try:
            resource_dir = importlib.resources.files(self._package_anchor)
            for item in resource_dir.iterdir():
                if item.is_file() and item.name.endswith(".md"):
                    profiles.add(item.name[:-3].lower())
        except (ImportError, TypeError, AttributeError, OSError):
            pass

        # Safeguard fallback if no files could be indexed
        if len(profiles) <= 1:
            return ["disabled", "general", "study", "translation", "writing"]

        return sorted(profiles)

    def load_profile(self, name: str) -> str:
        """
        Loads the contents of a specific markdown profile.

        Looks into the external user configuration profiles directory first, then
        falls back to internal embedded package resources. The special "disabled" profile
        intentionally returns an empty system prompt. Unknown profiles safely fall
        back to "general".
        """
        clean_name = name.lower().strip()

        if clean_name == "disabled":
            return ""

        filename = f"{clean_name}.md"

        # 1. Attempt to load from the external user configuration directory
        try:
            user_path = self.user_profiles_dir / filename
            if user_path.is_file():
                return user_path.read_text(encoding="utf-8").strip()
        except OSError:
            pass

        # 2. Fallback: Attempt to load from internal embedded package resources
        try:
            resource_path = importlib.resources.files(self._package_anchor) / filename
            if resource_path.is_file():
                return resource_path.read_text(encoding="utf-8").strip()
        except (ImportError, TypeError, AttributeError, OSError):
            pass

        if clean_name != "general":
            return self.load_profile("general")

        return ""
