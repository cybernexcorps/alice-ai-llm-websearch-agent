# 0001. Tool-call step detection contract for the Yandex Agent Atelier loop

## Status

Accepted

## Context

`AgentRunner.run()` (`agent.py`) wraps the Yandex AI Studio Agent Atelier via the OpenAI Responses API. The agent has WebSearch built in server-side, but the server does **not** emit typed `function_call` / `web_search_call` items in `response.output`. Instead, when the agent needs to make a tool call, the server inlines the tool-call step as literal JSON text directly in `response.output_text`, list-wrapped and keyed by `"function"` (legacy responses use `"name"`), e.g.:

```json
[ { "function": "web_search", "arguments": { "lang": "ru", "query": "..." } } ]
```

`run()` must detect this intermediate step via `_is_tool_call_response()` and continue the loop with `previous_response_id` plus a continuation prompt (`"Продолжи и дай финальный ответ."`), up to `_MAX_LOOP = 4` actual API calls. If detection fails, the raw JSON leaks straight to the user.

This was a real production bug affecting both Chat and Search: the detector matched only the substring `"name"`, but the server was emitting `"function"` instead. The bug shipped with a fully green test suite, because the test fixtures were written to match the buggy detector's substring check rather than captured from real Yandex responses — the tests validated the implementation, not the contract.

## Decision

Detection of a tool-call step is **structural**, not a bare substring match:

1. Parse balanced JSON candidates out of `output_text` (the payload may be embedded inside other text).
2. For each candidate, check tool-call shape: `function` or `name` field equals `"web_search"` **and** an `arguments`/`parameters` object is present.
3. Fall back to a whitespace-insensitive regex only as a secondary signal, never as the primary detection mechanism.

Canonical payload fixtures live in exactly one place: `tests/fixtures/yandex_responses.py`, and must be captured from real Yandex responses (not hand-written to match detector internals).

A symptom-level canary test, `tests/test_agent_contract.py`, asserts that `run()` never returns raw tool-call JSON to the caller — independent of `_is_tool_call_response`'s internals. This is the test that would have caught the production bug.

`run()` logs `CONTRACT_DRIFT` at error level whenever the final output still looks like tool-call JSON, or the loop exhausts `_MAX_LOOP` without resolving to a final answer.

A future structured-output detection path (checking typed item types in `response.output`) is deferred until a live Yandex response is confirmed to actually populate typed items — as of this decision, the API has not been observed to do so.

## Consequences

- Any change to `_is_tool_call_response` MUST add or adjust a fixture in `tests/fixtures/yandex_responses.py` captured from a real (or faithfully reproduced) Yandex response, and MUST keep `tests/test_agent_contract.py` passing.
- Fixture-only test changes that don't reflect an actual server payload are not acceptable evidence that detection works — they previously masked this exact bug.
- Referencing this ADR (`docs/adr/0001-tool-call-step-detection-contract.md`) from the `_is_tool_call_response` docstring is recommended so future edits find this contract before changing detection logic.
- The structural approach is more expensive than a substring check but is resilient to key renames (`name` → `function`) and to the payload being embedded in surrounding text.
