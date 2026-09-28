"""
api/routes/chat.py
-------------------
POST /chat — Natural-language weather query endpoint.

Full pipeline
-------------
1. Validate ChatRequest (Pydantic).
2. Assign / echo conversation_id (generate UUID if absent).
3. Retrieve conversation history from ContextService.
4. Extract intent (IntentService — deterministic, no LLM call).
5. Run tools and generate answer (LLMService — LLM or fallback).
6. Append user + assistant messages to ContextService.
7. Return ChatResponse.

Singletons
----------
All stateless service instances are module-level singletons.
ContextService is module-level because it holds in-memory state.
LLMService is initialised once from settings on startup.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.context_service import ContextService
from app.services.intent_service import IntentService
from app.services.llm_service import LLMService

router = APIRouter(tags=["Chat"])

# --------------------------------------------------------------------------- #
# Service singletons                                                           #
# --------------------------------------------------------------------------- #

_intent_service  = IntentService()
_context_service = ContextService()
_llm_service     = LLMService(
    api_key  = settings.LLM_API_KEY,
    model    = settings.LLM_MODEL,
    provider = settings.LLM_PROVIDER,
)


# --------------------------------------------------------------------------- #
# Endpoint                                                                     #
# --------------------------------------------------------------------------- #

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Natural-language weather query",
    description=(
        "Ask any weather, risk, or advisory question in plain English. "
        "Provide pre-fetched WeatherData in the request for context-aware answers. "
        "When the LLM API key is configured, answers are LLM-generated and grounded "
        "in real structured data. Without a key, the service returns template-based "
        "answers in 'fallback' mode (clearly indicated in the response). "
        "Conversation history is maintained per conversation_id for multi-turn dialogues."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a natural-language weather question end-to-end.

    Parameters
    ----------
    request:
        ChatRequest with message, optional location, conversation_id,
        and optional WeatherData.

    Returns
    -------
    ChatResponse:
        Grounded answer, source list, mode ('llm' or 'fallback'), and intent.
    """
    # ------------------------------------------------------------------ #
    # 1. Conversation identity                                             #
    # ------------------------------------------------------------------ #
    conv_id = request.conversation_id or str(uuid.uuid4())

    # ------------------------------------------------------------------ #
    # 2. Conversation history                                              #
    # ------------------------------------------------------------------ #
    history = _context_service.get_history(conv_id)

    # ------------------------------------------------------------------ #
    # 3. Intent extraction (deterministic — always runs)                  #
    # ------------------------------------------------------------------ #
    intent = _intent_service.extract(request.message)

    # ------------------------------------------------------------------ #
    # 4. Tool execution + answer generation (LLM or fallback)             #
    # ------------------------------------------------------------------ #
    answer, sources, mode = await _llm_service.respond(
        user_message = request.message,
        weather_data = request.weather_data,
        intent       = intent,
        history      = history,
    )

    # ------------------------------------------------------------------ #
    # 5. Persist conversation turn                                         #
    # ------------------------------------------------------------------ #
    _context_service.add_message(
        conv_id,
        ChatMessage(role="user", content=request.message),
    )
    _context_service.add_message(
        conv_id,
        ChatMessage(role="assistant", content=answer),
    )

    # ------------------------------------------------------------------ #
    # 6. Return response                                                   #
    # ------------------------------------------------------------------ #
    return ChatResponse(
        conversation_id = conv_id,
        answer          = answer,
        sources         = sources,
        mode            = mode,
        intent          = intent.intent,
    )
