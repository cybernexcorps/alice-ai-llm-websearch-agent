"""These payloads ARE the contract with the Yandex Agent Atelier server.
If the server changes format, update here — every test recompiles against
reality. See docs/adr for the tool-call detection contract.
"""

from __future__ import annotations

# Tool call response text (no final answer)
TOOL_CALL_TEXT = (
    'Выполню поиск.\n\n'
    '{"name":"web_search","description":"...","parameters":{}}\n\n'
    '{"lang":"ru","query":"конкуренты DDVB"}'
)

FINAL_ANSWER = "Конкуренты DDVB: агентство A, агентство Б..."

# Real production tool-call payload captured from Yandex Agent Atelier
# (list-wrapped, uses "function" key instead of "name" — this is the shape
# that shipped a bug because _is_tool_call_response() only checked "name").
TOOL_CALL_TEXT_REAL = (
    '[ { "function": "web_search", "arguments": '
    '{ "lang": "ru", "query": "авторские статьи о дизайне и брендинге" } } ]'
)
