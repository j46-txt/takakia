"""
Dynamic System Prompt Profile Subsystem.

Loads, caches, and enumerates system prompt instructions from embedded package markdown 
resources using standard platform resource abstractions.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Optional


class ProfileManager:
    """Discovers and retrieves Markdown system prompt profiles stored within the application."""

    def __init__(self) -> None:
        # Reference the current subpackage package anchor dynamically
        self._package_anchor = "takakia.profiles"

    def list_profiles(self) -> list[str]:
        """
        Dynamically enumerates all available prompt profile names.
        
        Scans the package resource directory for markdown files and returns
        their base names sorted alphabetically.
        """
        profiles: list[str] = []
        try:
            # importlib.resources.files is standard and safe across Python 3.9+
            resource_dir = importlib.resources.files(self._package_anchor)
            for item in resource_dir.iterdir():
                if item.is_file() and item.name.endswith(".md"):
                    # Strip the extension to get the profile handle (e.g. 'study') and normalize to lowercase
                    profiles.append(item.name[:-3].lower())
        except (ImportError, TypeError, AttributeError, OSError):
            # Fallback to standard safety defaults if resource tracking fails or access is denied
            return ["general", "study", "translation", "writing"]
            
        return sorted(list(set(profiles)))

    def load_profile(self, name: str) -> str:
        """
        Loads the contents of a specific markdown profile by name.
        
        Falls back to loading the 'general' profile if the requested profile 
        does not exist or cannot be accessed.
        """
        clean_name = name.lower().strip()
        filename = f"{clean_name}.md"
        
        try:
            resource_path = importlib.resources.files(self._package_anchor) / filename
            if resource_path.is_file():
                return resource_path.read_text(encoding="utf-8").strip()
        except (ImportError, TypeError, AttributeError, OSError):
            pass

        # Primary safe fallback chain if a user calls a non-existent or corrupted profile
        if clean_name != "general":
            return self.load_profile("general")
            
        return "You are a helpful, direct, and intelligent AI assistant."