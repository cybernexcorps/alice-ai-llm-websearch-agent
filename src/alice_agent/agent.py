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

import json
import logging
import re

import openai

from alice_agent.config import AGENT_BASE_URL, Settings, get_settings

logger = logging.getLogger(__name__)

# Max agent loop iterations (each iteration = one responses.create() call)
_MAX_LOOP = 4


def _is_tool_call_shape(obj: object) -> bool:
    """Return True if `obj` structurally looks like a web_search tool-call step.

    Accepts either a single dict or a list of dicts. Every element must be a
    dict whose "function" or "name" value is "web_search" AND which carries
    an "arguments" or "parameters" key (distinguishing a real tool-call step
    from a benign object that merely happens to have a "name" field).
    """
    if isinstance(obj, dict):
        items = [obj]
    elif isinstance(obj, list) and obj:
        items = obj
    else:
        return False

    for item in items:
        if not isinstance(item, dict):
            return False
        is_web_search = item.get("function") == "web_search" or item.get("name") == "web_search"
        has_args = "arguments" in item or "parameters" in item
        if not (is_web_search and has_args):
            return False
    return True


def _extract_json_candidates(text: str) -> list[str]:
    """Scan `text` for balanced top-level JSON array/object substrings.

    Uses a simple bracket-depth scan over `[]{}` (ignoring brackets inside
    string literals) and returns each complete top-level `[...]`/`{...}`
    span found, in order of appearance.
    """
    candidates: list[str] = []
    depth = 0
    start: int | None = None
    in_string = False
    escape = False
    opener: str | None = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch in "[{":
            if depth == 0:
                start = i
                opener = ch
            depth += 1
        elif ch in "]}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidates.append(text[start : i + 1])
                    start = None
                    opener = None

    return candidates


_TOOL_CALL_FALLBACK_RE = re.compile(
    r'("function"|"name")\s*:\s*"web_search".{0,500}?("arguments"|"parameters")\s*:',
    re.DOTALL,
)


def _is_tool_call_response(text: str) -> bool:
    """Return True if the response is an unfinished tool call with no final answer.

    The Yandex agent generates tool calls as JSON text before executing them.
    The real Agent Atelier server emits a list-wrapped step keyed by
    "function", e.g.:
        [{"function": "web_search", "arguments": {"lang": "ru", "query": "..."}}]
    An older/alternate shape keyed by "name" is kept as a fallback for
    compatibility:
        "I'll search...\n\n{\"name\":\"web_search\",...}\n\n{\"query\":\"...\"}"

    Detection is structural: JSON substrings are extracted and parsed, and
    only shapes that actually match a tool-call step (name/function ==
    "web_search" plus an arguments/parameters key) count. This avoids the
    false positives of a naive substring search, which would misfire on a
    final answer that merely quotes JSON containing a "name" key.
    """
    stripped = text.strip()
    if not stripped:
        return False

    for candidate in _extract_json_candidates(stripped):
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if _is_tool_call_shape(obj):
            return True

    return bool(_TOOL_CALL_FALLBACK_RE.search(stripped))


_WEB_SEARCH_MENTION_RE = re.compile(r'("function"|"name")\s*:\s*"web_search"')


def _looks_like_web_search_payload(text: str) -> bool:
    """Cheap, independent sanity check for defense-in-depth logging.

    Unlike `_is_tool_call_response`, this does not require the full
    tool-call shape — it just flags any mention of a web_search
    name/function key, so contract drift is caught even if the structural
    detector's shape assumptions no longer match the server's payload.
    """
    return bool(_WEB_SEARCH_MENTION_RE.search(text))


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
                if _looks_like_web_search_payload(text):
                    logger.error(
                        "CONTRACT_DRIFT: response still resembles tool-call JSON "
                        "after loop; format may have changed"
                    )
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
        logger.error(
            "CONTRACT_DRIFT: response still resembles tool-call JSON after loop; "
            "format may have changed"
        )
        return "Агент не смог завершить поиск. Попробуй переформулировать запрос."
