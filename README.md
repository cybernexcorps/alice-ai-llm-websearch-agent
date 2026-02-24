# Alice Agent — AI Web Search Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-package_manager-7C3AED?style=for-the-badge&logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![FastAPI](https://img.shields.io/badge/FastAPI-web-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Typer](https://img.shields.io/badge/Typer-CLI-1DA462?style=for-the-badge&logo=typer&logoColor=white)](https://typer.tiangolo.com/)
[![Yandex AI](https://img.shields.io/badge/Yandex_AI-Studio-FC3F1D?style=for-the-badge&logo=yandex&logoColor=white)](https://yandex.cloud/en/services/yandexgpt)
[![Tests](https://img.shields.io/badge/tests-104_passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](./tests/)

CLI-агент для PR-команды **DDVB** на базе **Alice AI LLM** (Yandex AI Studio).
Поиск в российском интернете встроен в агента — отдельный API поиска не нужен.

Требования: Python >= 3.11, [uv](https://docs.astral.sh/uv/).

---

## Быстрый старт

### 1. Установить зависимости

```bash
uv sync
```

### 2. Настроить окружение

```bash
cp .env.example .env
```

Заполни `.env` — нужен **один ключ**:

```env
ALICE_YC_API_KEY=<ваш-api-ключ-yandex-cloud>
```

Остальные значения уже прописаны по умолчанию.

### 3. Проверить конфигурацию

```bash
uv run alice version
```

---

## Использование

### Одиночный запрос

```bash
uv run alice search "Какие тренды в брендинге в 2026 году?"
uv run alice search "Конкуренты DDVB на рынке брендинга"

# Сохранить результат в JSON (поля: query, answer, timestamp)
uv run alice search "Конкуренты DDVB" --output results/competitors.json

# Сохранить результат в Markdown (H1-заголовок + ответ + timestamp)
uv run alice search "Тренды брендинга 2026" --output reports/trends.md

# Подробный вывод (шаги агента, без шума от сторонних библиотек)
uv run alice search "Тренды брендинга" --verbose
```

Флаг `--output` (`-o`) — путь к файлу. Формат определяется расширением: `.json` или `.md`.
Родительские директории создаются автоматически.

### Одиночный запрос с продолжением диалога

Если промт просит ИИ задать уточняющие вопросы перед ответом — используй флаг `--interactive` (`-i`).
После первого ответа Алисы CLI не завершается, а ждёт твоего ввода:

```bash
uv run alice search "Большой аналитический промт..." --interactive
uv run alice search "..." -i
```

Команды внутри интерактивного режима:
- `/new` — начать новый разговор (сбрасывает историю)
- `/quit` — выйти

### Интерактивный чат (с памятью разговора)

Полноценный REPL без начального запроса — удобен для свободного диалога:

```bash
uv run alice chat
```

Команды в чате:
- `/new` — начать новый разговор (сбрасывает историю)
- `/quit` — выйти

### Извлечь текст со страницы

```bash
uv run alice fetch https://sostav.ru/publication/example
```

### Веб-интерфейс

```bash
uv run alice web
# Открыть http://127.0.0.1:8080
```

Браузерный SPA с четырьмя вкладками: **Поиск**, **Чат**, **Извлечение**, **Конфигурация**.

- **Поиск** — веб-поиск с рендерингом Markdown. После получения результата кнопка **«Новый поиск»** сбрасывает форму без перезагрузки страницы. Экспорт в JSON и Markdown.
- **Чат** — многоходовой диалог с историей (кнопка «Новый разговор» сбрасывает сессию).
- **Извлечение** — извлечь текст веб-страницы по URL.
- **Конфигурация** — текущие настройки агента, статус API ключа.

Горячие клавиши: `Alt+1` … `Alt+4` — переключение вкладок. `Ctrl+Enter` в полях поиска и чата — отправить.

---

## Конфигурация

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `ALICE_YC_API_KEY` | — | Yandex Cloud API ключ **(обязательно)** |
| `ALICE_YC_FOLDER_ID` | `b1g6co0cfokq8k24mu7n` | ID каталога Yandex Cloud |
| `ALICE_YC_PROMPT_ID` | `fvtvl13pf2lknmsk33to` | ID агента в Agent Atelier |
| `ALICE_MAX_AGENT_STEPS` | `15` | Допустимый диапазон: 1–50. Отображается в `alice version`; фактический лимит вызовов API на один запрос — 4 |
| `ALICE_VERBOSE` | `false` | Включить подробное логирование по умолчанию |

---

## Архитектура

Агент работает полностью на стороне Yandex AI Studio. WebSearch встроен в агента `fvtvl13pf2lknmsk33to` — настроен с регионом 225 (Россия) и контекстом High.

```
User CLI
    │
    ▼
Typer CLI (alice search / chat / fetch)
    │
    ▼
AgentRunner
    │
    └─── openai.OpenAI(base_url=rest-assistant.api.cloud.yandex.net/v1)
              │
              └─── responses.create(
                       prompt={"id": "<agent_id>"},
                       input=query,
                       previous_response_id=...   ← multi-turn
                   )
                        │
                        ▼
              Yandex AI Studio Agent
                   Model: Alice AI LLM
                   Tool: WebSearch (встроен, регион RU)
```

**Цикл агента.** Иногда сервер возвращает ответ после первого шага модели (JSON с вызовом инструмента, без финального текста). `AgentRunner` обнаруживает это и продолжает цикл с `previous_response_id`, пока не получит финальный ответ или не исчерпает лимит (4 вызова на один запрос).

**Многоходовая беседа.** `previous_response_id` передаётся между вызовами `run()` — история хранится на стороне Yandex Cloud. `/new` в чате сбрасывает этот идентификатор.

### Структура файлов

```
src/alice_agent/
├── cli.py          # Typer CLI: search (--output, --verbose, --interactive), chat, fetch, web, version
├── agent.py        # AgentRunner, _is_tool_call_response, цикл responses.create
├── config.py       # Pydantic Settings (ALICE_ prefix), синглтон get_settings()
├── export.py       # Экспорт результатов в .json или .md
├── output.py       # Rich-форматирование консольного вывода
├── prompts.py      # Локальный системный промпт (справочно)
├── tools/
│   └── web_fetch.py    # Утилита: извлечение текста со страницы по URL
└── web/            # FastAPI веб-сервер (alice web → http://127.0.0.1:8080)

static/
├── fonts/          # Atyp Display + Atyp Text (self-hosted .ttf)
├── css/alice.css   # DDVB brand: white / #000 / #FDB71C, Atyp шрифты
├── index.html      # SPA-оболочка
└── js/             # Роутер (app.js), API (api.js), компоненты, вьюхи
```

---

## Разработка

```bash
# Установка с dev-зависимостями (pytest, pytest-mock, respx)
uv sync --extra dev

# Все тесты
uv run pytest tests/ -v

# Отдельные файлы
uv run pytest tests/test_agent.py -v
uv run pytest tests/test_export.py -v
uv run pytest tests/test_tools.py -v
uv run pytest tests/test_llm.py -v
```

---

## Получение API ключа

1. Перейди на [console.yandex.cloud](https://console.yandex.cloud)
2. IAM → Сервисные аккаунты → создай аккаунт с ролью `ai.languageModels.user`
3. Создай API ключ → скопируй в `.env` как `ALICE_YC_API_KEY`

---

## Безопасность

- API ключ хранится только в `.env`, файл включён в `.gitignore`
- Ключ обёрнут в `SecretStr` — не попадает в логи и вывод
- URL в `fetch_webpage` проходят валидацию: блокируются `localhost`, приватные IP, нестандартные схемы
- Все запросы к API — только по HTTPS
