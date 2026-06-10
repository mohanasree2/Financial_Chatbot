"""
gemini_client.py — Production-grade Gemini GenAI API integration module.
Handles all API interactions, error handling, logging, and token management.
Completely separated from UI code.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai
from loguru import logger

from prompts import (
    SYSTEM_PROMPT,
    FALLBACK_MESSAGE,
    ERROR_MESSAGES,
    CONTEXT_WINDOW_TURNS,
    SUMMARY_PROMPT,
)

# ── Logging Configuration ──────────────────────────────────────────────────────
logger.add(
    "logs/chatbot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str       # "user" or "model"
    content: str

@dataclass
class ChatResponse:
    text: str
    success: bool
    error: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

@dataclass
class SessionStats:
    total_turns: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_errors: int = 0
    session_start: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def session_duration_mins(self) -> float:
        return round((time.time() - self.session_start) / 60, 1)


# ── Gemini Client ──────────────────────────────────────────────────────────────

class GeminiChatClient:
    """
    Production-ready wrapper around the Gemini GenerativeAI API.
    Handles authentication, multi-turn context, error recovery, and logging.
    """

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self):
        load_dotenv()
        self._api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self._model: Optional[genai.GenerativeModel] = None
        self._chat_session = None
        self.stats = SessionStats()
        self._conversation_history: list[Message] = []

        self._initialize_client()

    # ── Initialization ─────────────────────────────────────────────────────────

    def _initialize_client(self) -> None:
        """Configure Gemini API with secure key management."""
        if not self._api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            raise EnvironmentError(ERROR_MESSAGES["api_key_missing"])

        try:
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=1024,
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ],
            )
            self._start_new_chat_session()
            logger.info(f"Gemini client initialized — model: {self.MODEL_NAME}")
        except Exception as e:
            logger.critical(f"Failed to initialize Gemini client: {e}")
            raise

    def _start_new_chat_session(self) -> None:
        """Start a fresh multi-turn chat session."""
        self._chat_session = self._model.start_chat(history=[])
        logger.info("New chat session started.")

    # ── Core API Call ──────────────────────────────────────────────────────────

    def send_message(self, user_message: str) -> ChatResponse:
        """
        Send a user message to Gemini and return a structured ChatResponse.
        Handles errors, logs all API calls, and tracks token usage.
        """
        if not user_message.strip():
            return ChatResponse(text="Please type a message.", success=False)

        logger.info(f"User message (turn {self.stats.total_turns + 1}): {user_message[:80]}...")
        start_time = time.time()

        # Token optimization: summarize context if conversation is long
        if self.stats.total_turns > 0 and self.stats.total_turns % CONTEXT_WINDOW_TURNS == 0:
            self._compress_context()

        try:
            response = self._chat_session.send_message(user_message)
            latency_ms = round((time.time() - start_time) * 1000, 1)

            # Extract token usage
            input_tokens = 0
            output_tokens = 0
            try:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
            except Exception:
                pass  # Token metadata not always available

            # Update session stats
            self.stats.total_turns += 1
            self.stats.total_input_tokens += input_tokens
            self.stats.total_output_tokens += output_tokens

            # Store in local history
            self._conversation_history.append(Message(role="user", content=user_message))
            self._conversation_history.append(Message(role="model", content=response.text))

            logger.info(
                f"Response received | tokens: {input_tokens}in/{output_tokens}out "
                f"| latency: {latency_ms}ms"
            )

            return ChatResponse(
                text=response.text,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )

        except genai.types.generation_types.BlockedPromptException as e:
            logger.warning(f"Prompt blocked by safety filters: {e}")
            self.stats.total_errors += 1
            return ChatResponse(
                text="⚠️ Your message was flagged by safety filters. Please rephrase your question.",
                success=False,
                error="blocked_prompt",
            )

        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            self.stats.total_errors += 1
            error_str = str(e).lower()

            # Log full error details for debugging
            logger.error(f"API error (turn {self.stats.total_turns}): {type(e).__name__}: {e}")

            if "429" in error_str or "quota exceeded" in error_str or "rate limit" in error_str or "resource_exhausted" in error_str:
                error_msg = ERROR_MESSAGES["rate_limit"]
                error_type = "rate_limit"
            elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
                error_msg = ERROR_MESSAGES["network_error"]
                error_type = "network_error"
            elif "not found" in error_str or "404" in error_str or "invalid" in error_str:
                error_msg = "⚠️ Model not found or invalid API request. Check your Gemini model name and API key."
                error_type = "invalid_request"
            else:
                error_msg = ERROR_MESSAGES["general"]
                error_type = "general"

            return ChatResponse(
                text=f"{error_msg}\n\n{FALLBACK_MESSAGE}",
                success=False,
                error=error_type,
                latency_ms=latency_ms,
            )

    # ── Context Management ────────────────────────────────────────────────────

    def _compress_context(self) -> None:
        """
        Token optimization: summarize old conversation to reduce context size.
        Called automatically after CONTEXT_WINDOW_TURNS turns.
        """
        logger.info("Compressing conversation context for token optimization...")
        try:
            summary_response = self._chat_session.send_message(SUMMARY_PROMPT)
            summary = summary_response.text

            # Restart chat session with compressed context injected
            self._chat_session = self._model.start_chat(history=[])
            self._chat_session.send_message(
                f"[Conversation Summary for continuity]\n{summary}\n"
                f"[End of summary — continue helping the user.]"
            )
            logger.info("Context compressed successfully.")
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            # Graceful fallback: just restart fresh
            self._start_new_chat_session()

    def reset_session(self) -> None:
        """Reset the chat session and all stats."""
        self._start_new_chat_session()
        self.stats = SessionStats()
        self._conversation_history.clear()
        logger.info("Chat session reset by user.")

    @property
    def is_ready(self) -> bool:
        """Check if the client is properly initialized."""
        return self._model is not None and self._chat_session is not None
