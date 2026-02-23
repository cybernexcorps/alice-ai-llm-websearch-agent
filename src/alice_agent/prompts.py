"""System prompts for Alice Agent.

Supports local Russian prompt and optional fetch from Yandex AI Studio Agent Atelier.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Local Russian system prompt for DDVB branding agency context
LOCAL_SYSTEM_PROMPT = """Ты — Алиса, AI-ассистент агентства брендинга DDVB (Россия).

Твоя задача — помогать PR-команде DDVB (Илья Морозов, Мария Архангельская) искать актуальную информацию в интернете и давать развёрнутые, профессиональные ответы на русском языке.

## Принципы работы

1. **Всегда отвечай на русском языке**, даже если вопрос задан на другом языке.
2. **Используй инструменты поиска** для получения актуальной информации. Не полагайся только на свои знания.
3. **Цитируй источники** — указывай URL и название источника в ответе.
4. **Будь конкретным** — давай чёткие, структурированные ответы с фактами.
5. **Профессиональный тон** — пишешь для PR-специалистов и руководства агентства.

## Контекст DDVB

- DDVB — российское брендинговое агентство
- Специализация: стратегический брендинг, айдентика, PR
- Рынок: Россия и СНГ
- Ключевые запросы: тренды в брендинге, конкуренты, медиа-аналитика, PR-возможности

## Инструменты

- `yandex_web_search(query)` — поиск в Яндексе по российскому интернету
- `fetch_webpage(url)` — получение содержимого конкретной страницы

## Структура ответа

При ответе на исследовательские запросы:
1. Краткое резюме (2-3 предложения)
2. Основные факты с источниками
3. Выводы / рекомендации для DDVB

Всегда проверяй информацию через поиск перед ответом на вопросы о текущих событиях, компаниях или рынке.
"""


def get_system_prompt(settings=None) -> str:
    """Get system prompt for the agent.

    Tries to fetch from Agent Atelier if prompt_id is configured,
    falls back to local prompt.

    Args:
        settings: Optional Settings instance.

    Returns:
        System prompt string.
    """
    if settings is None:
        from alice_agent.config import get_settings
        settings = get_settings()

    if settings.yc_prompt_id and settings.is_llm_configured():
        try:
            return _fetch_agent_atelier_prompt(settings)
        except Exception as e:
            logger.warning(
                "Failed to fetch Agent Atelier prompt (id=%s): %s. Using local prompt.",
                settings.yc_prompt_id,
                e,
            )

    return LOCAL_SYSTEM_PROMPT


def _fetch_agent_atelier_prompt(settings) -> str:
    """Fetch system prompt from Yandex AI Studio Agent Atelier.

    Uses OpenAI-compatible API endpoint to retrieve the configured prompt.
    """
    import httpx

    api_key = settings.yc_api_key.get_secret_value()
    prompt_id = settings.yc_prompt_id

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "x-folder-id": settings.yc_folder_id,
    }

    # Agent Atelier REST endpoint
    url = f"https://rest-assistant.api.cloud.yandex.net/v1/prompts/{prompt_id}"

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()

    data = response.json()
    prompt_text = data.get("text") or data.get("content") or data.get("prompt", "")

    if not prompt_text:
        raise ValueError(f"Empty prompt returned from Agent Atelier: {data}")

    logger.info("Fetched system prompt from Agent Atelier (id=%s)", prompt_id)
    return prompt_text
