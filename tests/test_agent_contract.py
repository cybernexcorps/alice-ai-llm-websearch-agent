"""Symptom-level contract test: no raw tool-call JSON must ever reach the user.

This is defense in depth, independent of `_is_tool_call_response()` internals.
Even if the detector regresses, these tests catch raw JSON leaking through
`AgentRunner.run()`'s return value.
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock

from tests.fixtures.yandex_responses import FINAL_ANSWER, TOOL_CALL_TEXT_REAL, IMAGE_TOOL_CALL_TEXT


def _resp(response_id: str, output_text: str) -> MagicMock:
    m = MagicMock()
    m.id = response_id
    m.output_text = output_text
    return m


def _assert_clean(result: str) -> None:
    assert not re.search(r'"(function|name)"\s*:\s*"[^"]+"', result)
    assert not result.strip().startswith(("{", "["))


class TestNoRawJsonLeak:

    def test_tool_call_then_final_answer_is_clean(self, mock_settings):
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", TOOL_CALL_TEXT_REAL),
            _resp("r2", FINAL_ANSWER),
        ]

        result = runner.run("авторские статьи о дизайне и брендинге")

        assert result == FINAL_ANSWER
        _assert_clean(result)

    def test_image_generation_tool_call_then_final_answer_is_clean(self, mock_settings):
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", IMAGE_TOOL_CALL_TEXT),
            _resp("r2", FINAL_ANSWER),
        ]

        result = runner.run("нарисуй закат")

        assert result == FINAL_ANSWER
        _assert_clean(result)

    def test_loop_exhaustion_returns_fallback_not_json(self, mock_settings):
        from alice_agent.agent import AgentRunner, _MAX_LOOP

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.return_value = _resp(
            "rx", TOOL_CALL_TEXT_REAL
        )

        result = runner.run("вопрос")

        assert runner._client.responses.create.call_count == _MAX_LOOP
        assert result != TOOL_CALL_TEXT_REAL
        _assert_clean(result)
