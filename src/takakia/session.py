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
            max_chars_limit: Strict localized memory fence threshold (~10k tokens)
                            to preserve older hardware resource cycles.
        """
        self.max_chars_limit = max_chars_limit
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
        
        Applies a defensive sliding window truncation algorithm to keep the total
        payload size within the character limit before returning.
        """
        self._prune_history()
        # Returns a deep collection representation to insulate internal structures
        return [dict(message) for message in self._messages]

    def _prune_history(self) -> None:
        """
        Prunes conversation history when it exceeds the character limit.
        
        Tracks boundaries efficiently in O(N) to discard overflowing items
        while guaranteeing the system prompt is preserved and the remaining conversation 
        context always starts with a valid 'user' message turn.
        """
        has_system = bool(self._messages and self._messages[0]["role"] == "system")
        system_msg = self._messages[0] if has_system else None
        chat_messages = self._messages[1:] if has_system else self._messages[:]

        system_len = len(system_msg["content"]) if system_msg else 0
        total_chars = sum(len(m["content"]) for m in chat_messages) + system_len

        if total_chars <= self.max_chars_limit:
            return

        # Determine the exact slice index needed to bring total characters below the fence
        drop_idx = 0
        # Prevent the loop from dropping the final message (the current turn) entirely
        while drop_idx < len(chat_messages) - 1 and total_chars > self.max_chars_limit:
            total_chars -= len(chat_messages[drop_idx]["content"])
            drop_idx += 1

        remaining_chat = chat_messages[drop_idx:]

        # Enforce API conformity: sequence context must always start with a user message turn
        user_start_idx = 0
        while user_start_idx < len(remaining_chat) and remaining_chat[user_start_idx]["role"] != "user":
            user_start_idx += 1

        remaining_chat = remaining_chat[user_start_idx:]

        # Re-assemble the state safely without breaking vendor-side expectations
        if system_msg:
            self._messages = [system_msg] + remaining_chat
        else:
            self._messages = remaining_chat

    @property
    def message_count(self) -> int:
        """Returns the total number of items inside the conversation log tracker."""
        return len(self._messages)