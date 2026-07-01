"""Tests for Alice Agent (Yandex AI Studio Responses API)."""

from __future__ import annotations

import openai
import pytest
from unittest.mock import MagicMock, call

from tests.fixtures.yandex_responses import (
    FINAL_ANSWER,
    TOOL_CALL_TEXT,
    TOOL_CALL_TEXT_REAL,
)


def _resp(response_id: str, output_text: str) -> MagicMock:
    m = MagicMock()
    m.id = response_id
    m.output_text = output_text
    return m


class TestAgentRunner:

    def test_runner_initializes(self, mock_settings):
        from alice_agent.agent import AgentRunner
        runner = AgentRunner(settings=mock_settings)
        assert runner.settings is mock_settings
        assert runner._previous_response_id is None

    def test_new_conversation_clears_id(self, mock_settings):
        from alice_agent.agent import AgentRunner
        runner = AgentRunner(settings=mock_settings)
        runner._previous_response_id = "resp_old"
        runner.new_conversation()
        assert runner._previous_response_id is None

    def test_run_single_step_answer(self, mock_settings):
        """When first response is a real answer, return it immediately."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.return_value = _resp("r1", FINAL_ANSWER)

        result = runner.run("вопрос")

        runner._client.responses.create.assert_called_once_with(
            prompt={"id": mock_settings.yc_prompt_id},
            input="вопрос",
        )
        assert result == FINAL_ANSWER

    def test_run_continues_loop_on_tool_call(self, mock_settings):
        """When first response is a tool call, loop continues to get real answer."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", TOOL_CALL_TEXT),
            _resp("r2", FINAL_ANSWER),
        ]

        result = runner.run("конкуренты DDVB")

        assert result == FINAL_ANSWER
        assert runner._client.responses.create.call_count == 2

        # Second call must include previous_response_id
        second_kwargs = runner._client.responses.create.call_args_list[1].kwargs
        assert second_kwargs["previous_response_id"] == "r1"

    def test_run_continues_loop_on_real_format_tool_call(self, mock_settings):
        """Regression: real Yandex tool-call shape (list-wrapped 'function' key)
        must be detected so the loop continues to a real answer, instead of
        returning the raw tool-call JSON as if it were the final answer."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", TOOL_CALL_TEXT_REAL),
            _resp("r2", FINAL_ANSWER),
        ]

        result = runner.run("авторские статьи о дизайне и брендинге")

        assert result == FINAL_ANSWER
        assert runner._client.responses.create.call_count == 2
        assert "web_search" not in result
        assert TOOL_CALL_TEXT_REAL not in result

    def test_run_saves_final_response_id(self, mock_settings):
        """previous_response_id should be set to the last response's id."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", TOOL_CALL_TEXT),
            _resp("r2", FINAL_ANSWER),
        ]

        runner.run("вопрос")
        assert runner._previous_response_id == "r2"

    def test_run_multi_turn_chains_ids(self, mock_settings):
        """Multi-turn: second run() uses id from first run's final response."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.side_effect = [
            _resp("r1", FINAL_ANSWER),
            _resp("r2", FINAL_ANSWER),
        ]

        runner.run("первый вопрос")
        runner.run("второй вопрос")

        second_call = runner._client.responses.create.call_args_list[1].kwargs
        assert second_call["previous_response_id"] == "r1"

    def test_run_exhausted_loop_returns_fallback(self, mock_settings):
        """When all loop iterations return tool calls, return fallback message."""
        from alice_agent.agent import AgentRunner, _MAX_LOOP

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.return_value = _resp("rx", TOOL_CALL_TEXT)

        result = runner.run("вопрос")

        assert runner._client.responses.create.call_count == _MAX_LOOP
        assert len(result) > 0  # Fallback message, not empty

    def test_run_exhausted_loop_clears_previous_response_id(self, mock_settings):
        """Loop exhaustion must not save the incomplete response id."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.return_value = _resp("rx", TOOL_CALL_TEXT)

        runner.run("вопрос")

        assert runner._previous_response_id is None

    def test_incomplete_bad_request_retries_without_prev_id(self, mock_settings):
        """BadRequestError with 'incomplete' clears prev_id and retries."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._previous_response_id = "stale_id"
        runner._client = MagicMock()

        incomplete_error = openai.BadRequestError(
            message="Previous response with id stale_id is in status incomplete, but must be COMPLETED",
            response=MagicMock(status_code=400),
            body={"error": {"message": "incomplete"}},
        )
        runner._client.responses.create.side_effect = [
            incomplete_error,
            _resp("r_fresh", FINAL_ANSWER),
        ]

        result = runner.run("вопрос")

        assert result == FINAL_ANSWER
        assert runner._client.responses.create.call_count == 2
        # Second call must NOT include previous_response_id
        second_kwargs = runner._client.responses.create.call_args_list[1].kwargs
        assert "previous_response_id" not in second_kwargs

    def test_other_bad_request_re_raises(self, mock_settings):
        """BadRequestError with non-incomplete message is re-raised."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()

        other_error = openai.BadRequestError(
            message="Invalid request: bad parameter",
            response=MagicMock(status_code=400),
            body={"error": {"message": "bad parameter"}},
        )
        runner._client.responses.create.side_effect = other_error

        with pytest.raises(openai.BadRequestError):
            runner.run("вопрос")

    def test_run_empty_output_returns_fallback(self, mock_settings):
        """Empty output_text should return fallback message."""
        from alice_agent.agent import AgentRunner

        runner = AgentRunner(settings=mock_settings)
        runner._client = MagicMock()
        runner._client.responses.create.return_value = _resp("r1", "")

        result = runner.run("вопрос")
        assert len(result) > 0

    def test_client_base_url(self, mock_settings):
        from alice_agent.agent import AgentRunner
        runner = AgentRunner(settings=mock_settings)
        assert runner.client.base_url.host == "rest-assistant.api.cloud.yandex.net"

    def test_client_project_is_folder_id(self, mock_settings):
        from alice_agent.agent import AgentRunner
        runner = AgentRunner(settings=mock_settings)
        assert runner.client.project == mock_settings.yc_folder_id


class TestToolCallDetection:

    def test_detects_web_search_tool_call(self):
        from alice_agent.agent import _is_tool_call_response
        assert _is_tool_call_response(TOOL_CALL_TEXT) is True

    def test_does_not_flag_real_answer(self):
        from alice_agent.agent import _is_tool_call_response
        assert _is_tool_call_response(FINAL_ANSWER) is False

    def test_does_not_flag_empty_string(self):
        from alice_agent.agent import _is_tool_call_response
        assert _is_tool_call_response("") is False

    def test_detects_name_with_spaces(self):
        from alice_agent.agent import _is_tool_call_response
        text = 'Поищу.\n\n{"name": "web_search", "parameters": {}}'
        assert _is_tool_call_response(text) is True

    def test_detects_real_function_format(self):
        """THE regression test: this is the exact production payload that the
        old detector (which only looked for "name":"web_search") missed."""
        from alice_agent.agent import _is_tool_call_response
        assert _is_tool_call_response(TOOL_CALL_TEXT_REAL) is True

    def test_detects_function_list_wrapped_no_spaces(self):
        from alice_agent.agent import _is_tool_call_response
        text = '[{"function":"web_search","arguments":{"lang":"ru","query":"тест"}}]'
        assert _is_tool_call_response(text) is True

    def test_detects_function_with_spaces(self):
        from alice_agent.agent import _is_tool_call_response
        text = '[ { "function": "web_search", "arguments": { "lang": "ru", "query": "тест" } } ]'
        assert _is_tool_call_response(text) is True

    def test_does_not_flag_normal_json_in_answer(self):
        from alice_agent.agent import _is_tool_call_response
        # A real answer mentioning JSON should not be flagged
        text = "API возвращает {\"status\": \"ok\", \"name\": \"DDVB\"}."
        assert _is_tool_call_response(text) is False

    def test_does_not_flag_function_key_in_answer(self):
        from alice_agent.agent import _is_tool_call_response
        # A real answer mentioning a "function" key unrelated to web_search
        # must not be flagged (mirrors the "name" false-positive guard).
        text = "Схема: {\"function\": \"format_date\", \"args\": {}}."
        assert _is_tool_call_response(text) is False


class TestSettings:

    def test_is_configured_true(self, mock_settings):
        assert mock_settings.is_configured() is True

    def test_is_configured_false(self, unconfigured_settings):
        assert unconfigured_settings.is_configured() is False

    def test_api_key_is_secret_str(self, mock_settings):
        from pydantic import SecretStr
        assert isinstance(mock_settings.yc_api_key, SecretStr)
        assert "test-api-key" not in str(mock_settings.yc_api_key)

    def test_max_steps_validation(self):
        import pytest
        from alice_agent.config import Settings
        with pytest.raises(Exception):
            Settings(max_agent_steps=0)
        with pytest.raises(Exception):
            Settings(max_agent_steps=100)

    def test_no_search_api_key_required(self, mock_settings):
        assert not hasattr(mock_settings, "yandex_search_api_key")

    def test_no_llm_backend_required(self, mock_settings):
        assert not hasattr(mock_settings, "llm_backend")
