"""
Conversation State and History Management Engine.

Maintains running conversational context streams, message payload compilation,
and automatic memory pruning limits to optimize local execution footprint.
"""

from __future__ import annotations

from typing import Optional


class ChatSession:
    """Manages the lifecycle, role assignments, and volume constraints of a chat thread."""

    def __init__(self, system_prompt: str, max_chars_limit: int = 40000) -> None:
        """
        Initializes a clean conversation state session thread.
        
        Args:
            system_prompt: Core operational guidelines for the model backend.
            max_chars_limit: Strict localized memory fence threshold (~10k tokens).
        """
        self.max_chars_limit = max(1000, max_chars_limit)
        self.system_prompt = system_prompt.strip()
        self._messages: list[dict[str, str]] = []
        self._initialize_stream()

    def _initialize_stream(self) -> None:
        """Injects the baseline layout configuration framing prompt into history."""
        self._messages = []
        if self.system_prompt:
            self._messages.append({"role": "system", "content": self.system_prompt})

    def add_message(self, role: str, content: str) -> None:
        """
        Appends a unique participant dialog payload item block into the history thread.
        
        Protects against system prompt boundaries manipulation by re-routing inputs.
        """
        clean_role = role.lower().strip()
        clean_content = content.strip()
        
        if not clean_content:
            return
            
        if clean_role == "system":
            self.update_system_prompt(clean_content)
        else:
            self._messages.append({"role": clean_role, "content": clean_content})

    def update_system_prompt(self, new_prompt: str) -> None:
        """
        Updates the active core instructions without resetting the chat history.
        
        Modifies or swaps the system prompt at the beginning of the chat thread.
        """
        self.system_prompt = new_prompt.strip()
        
        if self._messages and self._messages[0]["role"] == "system":
            if self.system_prompt:
                self._messages[0]["content"] = self.system_prompt
            else:
                self._messages.pop(0)
        elif self.system_prompt:
            self._messages.insert(0, {"role": "system", "content": self.system_prompt})

    def clear(self, alternative_prompt: Optional[str] = None) -> None:
        """
        Wipes the entire conversation history, resetting the chat thread.
        
        Optionally accepts a new system prompt configuration state choice.
        """
        if alternative_prompt is not None:
            self.system_prompt = alternative_prompt.strip()
        self._initialize_stream()

    def get_payload(self) -> list[dict[str, str]]:
        """
        Compiles and returns the conversation history optimized for the API request.
        
        Applies a non-mutating sliding window truncation algorithm to keep the total
        payload size within character limits without polluting persistent state.
        """
        return self._prune_history_copy()

    def _prune_history_copy(self) -> list[dict[str, str]]:
        """
        Generates a pruned copy of history without mutating internal state.
        """
        if not self._messages:
            return []

        # Create isolated deep-ish copies of dictionary elements
        working_messages = [{"role": m["role"], "content": m["content"]} for m in self._messages]

        has_system = bool(working_messages and working_messages[0]["role"] == "system")
        system_msg = working_messages[0] if has_system else None
        chat_messages = working_messages[1:] if has_system else working_messages[:]

        system_len = len(system_msg["content"]) if system_msg else 0
        
        # Guardrail against system prompts eating the entire memory limit
        if system_len > self.max_chars_limit * 0.8:
            system_msg["content"] = system_msg["content"][:int(self.max_chars_limit * 0.8)] + "\n[System: Profile truncated to preserve memory.]"
            system_len = len(system_msg["content"])

        total_chars = sum(len(m["content"]) for m in chat_messages) + system_len

        if total_chars <= self.max_chars_limit:
            return ([system_msg] + chat_messages) if system_msg else chat_messages

        # Drop oldest chat turns until character size limit is satisfied
        while len(chat_messages) > 1 and total_chars > self.max_chars_limit:
            total_chars -= len(chat_messages[0]["content"])
            chat_messages.pop(0)

        # Enforce API conformity: sequence context must start with a user message turn
        while chat_messages and chat_messages[0]["role"] != "user":
            total_chars -= len(chat_messages[0]["content"])
            chat_messages.pop(0)

        # Truncate remaining user message if total context still exceeds limit
        if total_chars > self.max_chars_limit and chat_messages:
            trunc_notice = "\n\n[System: Input truncated due to memory limits.]"
            safe_len = max(0, self.max_chars_limit - system_len - len(trunc_notice))
            chat_messages[0]["content"] = chat_messages[0]["content"][:safe_len] + trunc_notice

        return ([system_msg] + chat_messages) if system_msg else chat_messages

    @property
    def message_count(self) -> int:
        """Returns the total number of items inside the conversation log tracker."""
        return len(self._messages)
