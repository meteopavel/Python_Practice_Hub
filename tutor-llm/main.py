# -*- coding: utf-8 -*-
"""Tutor-LLM — прокси к DeepSeek API для тьютора.

Живёт на роутере (как executor), доступен только внутри тоннеля
(10.0.0.1:8011). Единственная задача: принять структурированный
запрос {task_context, student_code, question} от webapp'а на Frankfurt,
собрать промпт, сходить в DeepSeek, вернуть ответ. Ключ DEEPSEEK_API_KEY
живёт только в этом контейнере — наружу (во webapp, в браузер) не уходит.

В будущем здесь же вырастет RAG: добавится обращение к векторной БД,
промпт будет заземляться найденными чанками методики. Пока — чистый
LLM-вызов для проверки базовой связки end-to-end.
"""
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import httpx

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# Педагогический системный промпт — задаёт роль репетитора по
# информатике (ОГЭ/ЕГЭ). Один источник правды для всех запросов тьютора.
SYSTEM_PROMPT = (
    "Ты — тьютор по информатике (ОГЭ/ЕГЭ). Объясняешь ученику понятно, "
    "по делу, на русском. Если в вопросе есть код ученика — разбери, "
    "почему он работает или не работает, сошлись на конкретные строки. "
    "Не выдумывай факты: если не знаешь — скажи прямо. Отвечай кратко, "
    "без воды, без chain-of-thought в выводе."
)

app = FastAPI(title="Python Practice Hub — tutor-LLM")


class AskRequest(BaseModel):
    """Запрос от webapp'а. Все поля опциональны кроме question —
    тьютор может спрашивать и без контекста задачи."""
    task_context: str | None = None
    student_code: str | None = None
    question: str


def _build_user_message(req: AskRequest) -> str:
    """Собирает пользовательское сообщение из структурированных полей.
    Разделители --- чтобы модели было проще различать блоки."""
    parts = []
    if req.task_context:
        parts.append(f"Задание:\n{req.task_context}")
    if req.student_code:
        parts.append(f"Код ученика:\n```python\n{req.student_code}\n```")
    parts.append(f"Вопрос тьютора:\n{req.question}")
    return "\n\n---\n\n".join(parts)


@app.post("/ask")
def ask(payload: AskRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="DEEPSEEK_API_KEY не задан в окружении контейнера tutor-llm",
        )

    user_message = _build_user_message(payload)

    # OpenAI-compatible запрос к DeepSeek. reasoner-режим не включаем —
    # для ответов тьютора обычный chat быстрее и дешевле, а reasoning
    # добавим позже точечно для сложных разборов кода.
    deepseek_body = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 1000,
        "temperature": 0.5,
    }

    try:
        # 60 сек — разумный потолок для одного ответа тьютора.
        # DeepSeek-chat обычно отвечает за 2-10 сек.
        response = httpx.post(
            DEEPSEEK_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            },
            json=deepseek_body,
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # DeepSeek вернул HTTP-ошибку (401 — плохой ключ, 429 — лимит, и т.д.)
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek API error {exc.response.status_code}: "
                   f"{exc.response.text[:300]}",
        )
    except httpx.HTTPError as exc:
        # Сетевая ошибка (таймаут, DNS, connection refused).
        raise HTTPException(
            status_code=502,
            detail=f"Не удалось дойти до DeepSeek API: {exc}",
        )

    data = response.json()
    choice = data["choices"][0]["message"]

    return {
        "answer": choice.get("content", ""),
        "model": data.get("model", DEEPSEEK_MODEL),
        "finish_reason": data["choices"][0].get("finish_reason"),
        "usage": data.get("usage", {}),
    }


@app.get("/health")
def health():
    """Readiness-чек. Ключ НЕ отдаём наружу — только факт его наличия."""
    return {"ok": bool(DEEPSEEK_API_KEY), "model": DEEPSEEK_MODEL}
