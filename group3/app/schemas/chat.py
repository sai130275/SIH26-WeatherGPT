"""
schemas/chat.py
---------------
Pydantic models for Phase 5: LLM / AI Query Engine.

Data flow:
  POST /chat
    ↓
  ChatRequest  (message + optional location/weather_data/conversation_id)
    ↓
  IntentResult (extracted by IntentService — deterministic)
    ↓
  Tool results (from existing engines)
    ↓
  ChatResponse (LLM-grounded or fallback answer)

Mode field rules
----------------
  "llm"      → LLM_API_KEY was present and the API call succeeded.
  "fallback" → API key absent, or LLM call failed; answer is template-based.
               This MUST be surfaced to the caller — never silently pretend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.weather import WeatherData


# --------------------------------------------------------------------------- #
# Shared literals                                                              #
# --------------------------------------------------------------------------- #

IntentType = Literal["weather", "forecast", "risk", "advisory", "activity", "general"]

ChatMode = Literal["llm", "fallback"]

MessageRole = Literal["user", "assistant", "system"]


# --------------------------------------------------------------------------- #
# Location input                                                               #
# --------------------------------------------------------------------------- #

class LocationInput(BaseModel):
    """Lat/lon pair supplied by the client alongside a chat message."""

    latitude: float = Field(..., ge=-90, le=90, examples=[17.9689])
    longitude: float = Field(..., ge=-180, le=180, examples=[79.5941])


# --------------------------------------------------------------------------- #
# Conversation message                                                         #
# --------------------------------------------------------------------------- #

class ChatMessage(BaseModel):
    """A single turn in a conversation history."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp of the message.",
    )


# --------------------------------------------------------------------------- #
# Intent result (internal — not exposed in API response)                       #
# --------------------------------------------------------------------------- #

class IntentResult(BaseModel):
    """
    Structured intent extracted from the user's message by IntentService.

    Extraction is deterministic (keyword-based) — no LLM call is made here.
    """

    intent: IntentType = Field(
        ...,
        description="Primary intent category.",
        examples=["risk"],
    )
    activity: Optional[str] = Field(
        default=None,
        description="Specific activity mentioned (e.g. 'travel', 'farming').",
        examples=["travel"],
    )
    time_reference: Optional[str] = Field(
        default=None,
        description="Time phrase extracted from the message.",
        examples=["tomorrow evening"],
    )
    requires_weather_data: bool = Field(
        default=True,
        description=(
            "True when answering the question requires current weather observations. "
            "False for general/meta questions."
        ),
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the intent classification (0–1).",
    )


# --------------------------------------------------------------------------- #
# Chat request                                                                 #
# --------------------------------------------------------------------------- #

class ChatRequest(BaseModel):
    """
    Input payload for POST /chat.

    Group 2 (Node.js backend) sends:
      - The user's natural-language message.
      - The location (optional — helps contextualise weather answers).
      - An existing conversation_id to continue a session (optional).
      - Pre-fetched WeatherData (optional — if available from their weather source).

    If weather_data is None, the service can still answer general questions
    but will indicate that weather-specific answers are unavailable.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's natural-language question or statement.",
        examples=["Can I travel tomorrow evening?"],
    )
    location: Optional[LocationInput] = Field(
        default=None,
        description="User's location. Helps contextualise weather and risk answers.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing conversation ID to continue a session. "
            "If omitted, a new session is started and a fresh ID is returned."
        ),
        examples=["abc123"],
    )
    weather_data: Optional[WeatherData] = Field(
        default=None,
        description=(
            "Pre-fetched weather observation provided by Group 2. "
            "Used by the tool layer to calculate risk and advisories. "
            "If absent, weather-specific answers are unavailable."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Can I travel tomorrow evening?",
                "location": {"latitude": 17.9689, "longitude": 79.5941},
                "conversation_id": "abc123",
                "weather_data": {
                    "location": "Warangal",
                    "latitude": 17.9689,
                    "longitude": 79.5941,
                    "timestamp": "2026-09-28T10:00:00Z",
                    "temperature": 42.0,
                    "rainfall": 72.0,
                    "wind_speed": 85.0,
                    "visibility": 0.5,
                },
            }
        }
    }


# --------------------------------------------------------------------------- #
# Chat response                                                                #
# --------------------------------------------------------------------------- #

class ChatResponse(BaseModel):
    """
    Response returned by POST /chat.

    The `mode` field is ALWAYS present and ALWAYS truthful:
      - "llm"      → the answer was generated by the configured LLM.
      - "fallback" → the answer was generated by the deterministic template engine.

    Never silently pretend the LLM is working.
    """

    conversation_id: str = Field(
        ...,
        description="Session identifier. Echo of the request ID, or a generated UUID.",
        examples=["abc123"],
    )
    answer: str = Field(
        ...,
        description="Natural-language answer to the user's question.",
        examples=["Heavy rainfall is expected. Avoid unnecessary travel."],
    )
    sources: list[str] = Field(
        default_factory=list,
        description=(
            "Names of Group 3 services whose results informed the answer. "
            "Empty if the question could not be answered from structured data."
        ),
        examples=[["weather", "risk", "advisory"]],
    )
    mode: ChatMode = Field(
        ...,
        description=(
            "'llm' when the answer was LLM-generated; "
            "'fallback' when using deterministic templates (no API key or LLM failure)."
        ),
        examples=["fallback"],
    )
    intent: Optional[str] = Field(
        default=None,
        description="Detected intent category for debugging / transparency.",
        examples=["activity"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "abc123",
                "answer": "Current risk is HIGH due to heavy rainfall. Avoid unnecessary travel.",
                "sources": ["weather", "risk", "advisory"],
                "mode": "fallback",
                "intent": "activity",
            }
        }
    }
