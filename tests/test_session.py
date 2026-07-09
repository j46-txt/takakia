"""Verifies structural chat logs, system overrides, and character-based truncation boundaries."""

from __future__ import annotations

from takakia.session import ChatSession


def test_chat_session_initialization() -> None:
    """Ensures system prompts position correctly at the thread baseline index layout."""
    prompt_text = "Instruction Guide Matrix."
    session = ChatSession(system_prompt=prompt_text)
    
    assert session.system_prompt == prompt_text
    assert session.message_count == 1
    
    payload = session.get_payload()
    assert payload[0]["role"] == "system"
    assert payload[0]["content"] == prompt_text


def test_message_addition_accumulation() -> None:
    """Validates structural participant conversation dialog serialization tracks."""
    session = ChatSession(system_prompt="Base instruction.")
    
    session.add_message(role="user", content="Question Text String Data.")
    session.add_message(role="assistant", content="Answer Output.")
    
    assert session.message_count == 3
    payload = session.get_payload()
    
    assert payload[1]["role"] == "user"
    assert payload[1]["content"] == "Question Text String Data."
    assert payload[2]["role"] == "assistant"
    assert payload[2]["content"] == "Answer Output."


def test_dynamic_system_prompt_updates() -> None:
    """Ensures modifying system prompts transforms parameters without dropping user conversation rows."""
    session = ChatSession(system_prompt="Initial Guidelines.")
    session.add_message(role="user", content="Keep message intact.")
    
    session.update_system_prompt("Revised Directives.")
    assert session.system_prompt == "Revised Directives."
    assert session.message_count == 2
    
    payload = session.get_payload()
    assert payload[0]["role"] == "system"
    assert payload[0]["content"] == "Revised Directives."
    assert payload[1]["content"] == "Keep message intact."


def test_defensive_sliding_window_pruning() -> None:
    """Validates defensive character-limit pruning and user/assistant dialog structural consistency alignment."""
    # Create an artificial low threshold limit boundary fence (e.g., max 100 character footprint restriction)
    session = ChatSession(system_prompt="System Prompt Guidelines.", max_chars_limit=100)
    
    # Adding heavy payloads forcing character boundaries capacity exceptions allocations
    session.add_message(role="user", content="A" * 40)       # 40 chars
    session.add_message(role="assistant", content="B" * 40)  # 40 chars -> Total 80 + ~24 system = ~104 (Exceeds 100!)
    
    # Initial payloads fit or drop oldest entry pairs safely when accessed
    payload = session.get_payload()
    total_chars = sum(len(m["content"]) for m in payload)
    assert total_chars <= 100
    # Ensure system prompt is explicitly protected across cleanup transformations
    assert payload[0]["role"] == "system"