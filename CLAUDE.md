# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies (pytest, pytest-mock, respx)
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_agent.py -v

# Run the CLI
uv run alice search "Тренды брендинга 2026"
uv run alice chat
uv run alice fetch https://example.com
uv run alice version

# Run the web interface (opens at http://127.0.0.1:8080)
uv run alice web
```

## Architecture

This is a Python CLI tool (`typer` + `rich`) that wraps the **Yandex AI Studio Agent Atelier** via the OpenAI Responses API. The agent has WebSearch built in server-side — no separate search API key is required.

### Key architectural decisions

**OpenAI SDK → Yandex endpoint.** The `openai.OpenAI` client is pointed at `https://rest-assistant.api.cloud.yandex.net/v1`. The agent is identified by `yc_prompt_id` (an Agent Atelier agent ID), passed as `prompt={"id": ...}` to `responses.create()`.

**Agent loop (`agent.py:AgentRunner.run`).** The Yandex API sometimes returns an intermediate tool-call JSON step rather than the final answer. `_is_tool_call_response()` detects this by looking for `"name":"web_search"` in the normalized text. When detected, the loop continues with `previous_response_id` and a continuation prompt (`"Продолжи и дай финальный ответ."`). The loop cap is `_MAX_LOOP = 4` actual API calls.

**Multi-turn memory.** Conversation state lives server-side in Yandex Cloud. `AgentRunner._previous_response_id` threads the `previous_response_id` parameter between `run()` calls. `/new` in the CLI resets this field via `new_conversation()`. If a `BadRequestError` mentions "incomplete", the stale ID is discarded and the call is retried fresh.

**Configuration (`config.py`).** `pydantic-settings` with `ALICE_` env prefix, loaded from `.env`. The singleton pattern (`get_settings()` / `reset_settings()`) is used so tests can monkeypatch env vars cleanly — `reset_settings()` is called in `conftest.py`'s `autouse` fixture.

**Export (`export.py`).** Format is determined by file extension (`.json` or `.md`). Parent directories are created automatically. All files written with UTF-8 encoding.

**Web fetch (`tools/web_fetch.py`).** Standalone utility used by the `alice fetch` command. Text extraction uses trafilatura first, falls back to BeautifulSoup+lxml. Blocks localhost and RFC-1918 addresses. Content truncated at 4000 chars.

**Web interface (`alice web`).** FastAPI server serving `static/` at `http://127.0.0.1:8080`. Four views: Поиск, Чат, Извлечение, Конфигурация. SPA router in `static/js/app.js` manages view switching and nav state. All API calls go through `static/js/api.js` to backend routes in `src/alice_agent/web/`.

### Web interface structure

```
static/
├── fonts/          # Self-hosted Atyp Display + Atyp Text (.ttf)
├── css/alice.css   # DDVB brand: white/#000/#FDB71C, Atyp font, no glassmorphism
├── index.html      # SPA shell (JetBrains Mono from CDN; Atyp self-hosted)
└── js/
    ├── app.js                  # View router, keyboard shortcuts (Alt+1–4)
    ├── api.js                  # Fetch wrappers for all backend endpoints
    ├── components/
    │   ├── toast.js            # Toast notifications
    │   ├── loader.js           # Skeleton show/hide helpers
    │   └── markdown.js         # marked.js + DOMPurify rendering
    └── views/
        ├── search.js           # Search form, result card, export, reset ("Новый поиск")
        ├── chat.js             # Multi-turn chat, /new conversation
        ├── fetch.js            # URL text extraction
        └── config.js           # Lazy-loaded config panel
```

### CSS / design notes

- **Brand**: white background (`#FFF`), black text (`#000`), single accent `#FDB71C`. No other colors except `#DD4444` for API key error dot.
- **Fonts**: Atyp Display (headings, logo) + Atyp Text (body) via `@font-face` from `static/fonts/`. JetBrains Mono (CDN) for monospace only.
- **Active nav**: full `#FDB71C` background pill, black bold text. The `.tab-item--active` rule is scoped to `.tab-bar` to avoid color cascade onto sidebar nav buttons (JS adds both classes to all `[data-view]` elements).
- **`[hidden]` reset**: `[hidden] { display: none !important; }` is required because `.config-grid { display: grid }` otherwise overrides the UA `hidden` attribute, keeping skeleton loaders permanently visible.
- **Search layout**: `.search-form` capped at `max-width: 720px`; result card fills full content width (`.view` has no `max-width`).

### Testing patterns

Tests mock `runner._client` directly (bypass the `client` lazy property by assigning `runner._client = MagicMock()`). Use `_resp(id, text)` helper to build mock response objects. All tests in `conftest.py` get the `reset_settings_singleton` autouse fixture; use `mock_settings` fixture for a configured settings object.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues (using the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

