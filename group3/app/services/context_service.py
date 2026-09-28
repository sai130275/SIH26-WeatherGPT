"""
services/context_service.py
-----------------------------
In-memory conversation context store for the MVP.

Design principles
-----------------
* Thread-safe for single-process deployments (uses a plain dict for MVP).
* Conversations are identified by a string conversation_id.
* Each conversation stores only the most recent N messages (bounded memory).
* The public interface is designed so a persistent backend (Redis, MongoDB)
  can be dropped in later without changing any callers:
    get_history(), add_message(), clear(), list_ids()

MVP constraints
---------------
* In-memory only — data is lost on restart.
* No authentication or ownership check.
* NOT thread-safe for multi-process deployments; upgrade to Redis for that.
"""

from __future__ import annotations

from app.schemas.chat import ChatMessage


# Maximum number of messages stored per conversation.
# Older messages beyond this limit are dropped (FIFO).
_MAX_MESSAGES_PER_CONVERSATION: int = 20


class ContextService:
    """
    In-memory conversation context manager.

    Usage
    -----
    >>> ctx = ContextService()
    >>> ctx.add_message("abc", ChatMessage(role="user", content="Hi"))
    >>> ctx.get_history("abc")
    [ChatMessage(role='user', content='Hi', ...)]

    Swapping to a persistent backend
    ---------------------------------
    1. Create a class that exposes the same four methods:
       get_history(), add_message(), clear(), list_ids()
    2. Inject it wherever ContextService is currently used.
    """

    def __init__(self, max_messages: int = _MAX_MESSAGES_PER_CONVERSATION) -> None:
        self._max: int = max_messages
        # conversation_id → list of ChatMessage (oldest first)
        self._store: dict[str, list[ChatMessage]] = {}

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def get_history(self, conversation_id: str) -> list[ChatMessage]:
        """
        Return the message history for a conversation.

        Returns an empty list if the conversation_id is not known.
        The returned list is a copy — callers cannot mutate internal state.
        """
        return list(self._store.get(conversation_id, []))

    def add_message(self, conversation_id: str, message: ChatMessage) -> None:
        """
        Append a message to a conversation.

        If the conversation does not exist it is created automatically.
        If the conversation exceeds max_messages, the oldest message is dropped.
        """
        if conversation_id not in self._store:
            self._store[conversation_id] = []

        self._store[conversation_id].append(message)

        # Enforce the sliding window
        if len(self._store[conversation_id]) > self._max:
            self._store[conversation_id] = self._store[conversation_id][-self._max :]

    def clear(self, conversation_id: str) -> None:
        """Delete all messages for a conversation."""
        self._store.pop(conversation_id, None)

    def list_ids(self) -> list[str]:
        """Return all known conversation IDs."""
        return list(self._store.keys())

    def conversation_count(self) -> int:
        """Return the number of active conversations."""
        return len(self._store)

    def message_count(self, conversation_id: str) -> int:
        """Return the number of messages stored for a conversation."""
        return len(self._store.get(conversation_id, []))
