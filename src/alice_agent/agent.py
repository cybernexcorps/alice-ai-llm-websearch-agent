"""Alice Agent — wraps Yandex AI Studio Agent Atelier via Responses API.

The agent `fvtvl13pf2lknmsk33to` is configured in Agent Atelier with:
- Model: Alice AI LLM (Latest)
- WebSearch tool: High context, region 225 (Russia)
- System instruction: search-first assistant

Multi-turn conversation uses `previous_response_id` to maintain context.

Execution loop:
  responses.create() sometimes returns after the model's first step (tool call
  JSON, no answer). When detected, we continue with previous_response_id so
  the server executes the search and returns the synthesized answer.
"""

from __future__ import annotations

import logging

import openai

from alice_agent.config import AGENT_BASE_URL, Settings, get_settings

logger = logging.getLogger(__name__)

# Max agent loop iterations (each iteration = one responses.create() call)
_MAX_LOOP = 4


def _is_tool_call_response(text: str) -> bool:
    """Return True if the response is an unfinished tool call with no final answer.

    The Yandex agent generates tool calls as JSON text before executing them.
    A response that ends at this step looks like:
        "I'll search...\n\n{\"name\":\"web_search\",...}\n\n{\"query\":\"...\"}"
    """
    normalized = text.replace(": ", ":").replace(" :", ":")
    return '"name":"web_search"' in normalized


class AgentRunner:
    """High-level interface for running Alice AI Studio Agent."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._previous_response_id: str | None = None
        self._client: openai.OpenAI | None = None

    @property
    def client(self) -> openai.OpenAI:
        if self._client is None:
            api_key = self.settings.yc_api_key.get_secret_value()
            self._client = openai.OpenAI(
                api_key=api_key or "placeholder",
                base_url=AGENT_BASE_URL,
                project=self.settings.yc_folder_id,
            )
        return self._client

    def new_conversation(self) -> None:
        """Start a new conversation (clears session memory)."""
        self._previous_response_id = None
        logger.debug("New conversation started.")

    def run(self, query: str) -> str:
        """Run a query through the agent loop until a final answer is received.

        If the server returns a tool call step (WebSearch pending) instead of
        the final answer, continues the loop with previous_response_id until
        a real answer arrives or the loop limit is reached.

        Args:
            query: User query (Russian).

        Returns:
            Agent's final answer text.
        """
        current_input: str = query
        prev_id: str | None = self._previous_response_id

        for step in range(_MAX_LOOP):
            kwargs: dict = {
                "prompt": {"id": self.settings.yc_prompt_id},
                "input": current_input,
            }
            if prev_id:
                kwargs["previous_response_id"] = prev_id

            logger.debug(
                "Loop step %d: prompt_id=%s, prev=%s",
                step + 1, self.settings.yc_prompt_id, prev_id,
            )

            try:
                response = self.client.responses.create(**kwargs)
            except openai.BadRequestError as exc:
                if "incomplete" in str(exc).lower():
                    logger.warning(
                        "Previous response incomplete, starting fresh context."
                    )
                    prev_id = None
                    kwargs.pop("previous_response_id", None)
                    response = self.client.responses.create(**kwargs)
                else:
                    raise
            prev_id = response.id
            text = response.output_text or ""

            if not _is_tool_call_response(text):
                # Got a real answer — done
                self._previous_response_id = prev_id
                return text or "Не удалось получить ответ."

            logger.debug(
                "Step %d returned a tool call; continuing loop (prev_id=%s).",
                step + 1, prev_id,
            )
            # Pass previous_response_id so the server can execute the pending tool
            current_input = "Продолжи и дай финальный ответ."

        # Loop exhausted without a real answer — last response is incomplete, don't save it
        self._previous_response_id = None
        logger.warning("Agent loop exhausted after %d steps without a final answer.", _MAX_LOOP)
        return "Агент не смог завершить поиск. Попробуй переформулировать запрос."
