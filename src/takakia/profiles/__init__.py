"""
Dynamic System Prompt Profile Subsystem.

Loads, caches, and enumerates system prompt instructions from embedded package markdown
resources using standard platform resource abstractions.
"""

from __future__ import annotations

import importlib.resources


class ProfileManager:
    """Discovers and retrieves Markdown system prompt profiles stored within the application."""

    def __init__(self) -> None:
        self._package_anchor = "takakia.profiles"

    def list_profiles(self) -> list[str]:
        """
        Dynamically enumerates all available prompt profile names.

        Scans the package resource directory for markdown files and returns
        their base names sorted alphabetically. The special "disabled" profile
        is always available even though it has no backing markdown file.
        """
        profiles: set[str] = {"disabled"}

        try:
            resource_dir = importlib.resources.files(self._package_anchor)
            for item in resource_dir.iterdir():
                if item.is_file() and item.name.endswith(".md"):
                    profiles.add(item.name[:-3].lower())
        except (ImportError, TypeError, AttributeError, OSError):
            return ["disabled", "general", "study", "translation", "writing"]

        return sorted(profiles)

    def load_profile(self, name: str) -> str:
        """
        Loads the contents of a specific markdown profile.

        The special "disabled" profile intentionally returns an empty
        system prompt. Unknown profiles safely fall back to "general".
        """
        clean_name = name.lower().strip()

        if clean_name == "disabled":
            return ""

        filename = f"{clean_name}.md"

        try:
            resource_path = importlib.resources.files(self._package_anchor) / filename
            if resource_path.is_file():
                return resource_path.read_text(encoding="utf-8").strip()
        except (ImportError, TypeError, AttributeError, OSError):
            pass

        if clean_name != "general":
            return self.load_profile("general")

        return ""