# -*- coding: utf-8 -*-
"""Тьюторские API: проверка/запуск кода из редактора подсказки и прокси к
ИИ-ассистенту (DeepSeek через tutor-llm)."""
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from webapp.config import TUTOR_LLM_URL
from webapp.core.auth import current_user_id, current_user_role, forbidden, unauthorized
from webapp.grading.grading import grade, run_free
from webapp.routes._common import HintFreeRunRequest, SubmissionRequest

router = APIRouter()


def _require_tutor(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != "tutor":
        return forbidden()
    return None


class TutorAskRequest(BaseModel):
    """Запрос тьютора к ИИ-помощнику. task_context/student_code опциональны —
    можно спросить и без них. question обязателен."""
    task_context: str | None = None
    student_code: str | None = None
    question: str


@router.post("/api/hint/run")
def run_hint_code(payload: SubmissionRequest, request: Request):
    """Тьютор проверяет код прямо в редакторе подсказки — тот же grade(),
    но без записи Attempt: это демонстрация ученику, а не его попытка."""
    if (err := _require_tutor(request)) is not None:
        return err
    return grade(payload.task_id, payload.code)


@router.post("/api/hint/run_free")
def run_hint_code_free(payload: HintFreeRunRequest, request: Request):
    """Свободный запуск кода в подсказке — без сверки с эталоном, просто
    исполняет код как есть (print() и любые операторы отрабатывают)."""
    if (err := _require_tutor(request)) is not None:
        return err
    return run_free(payload.code)


@router.post("/api/tutor/ask")
def tutor_ask(payload: TutorAskRequest, request: Request):
    """Тьютор спрашивает ИИ-помощника (DeepSeek через микросервис tutor-llm
    на роутере). Прокси: webapp не знает ключ DeepSeek, он только пересылает
    структурированный запрос в tutor-llm по внутренней сети (как executor).
    Только для роли tutor."""
    if (err := _require_tutor(request)) is not None:
        return err

    try:
        response = httpx.post(
            f"{TUTOR_LLM_URL}/ask",
            json=payload.model_dump(),
            timeout=70.0,  # чуть больше, чем 60-секундный таймаут tutor-llm → DeepSeek
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        # tutor-llm ответил ошибкой (скорее всего 502 от DeepSeek или 500 — нет ключа)
        return JSONResponse(
            status_code=exc.response.status_code,
            content={"error": f"tutor-llm: {exc.response.text[:300]}"},
        )
    except httpx.HTTPError as exc:
        # tutor-llm недоступен (контейнер не поднят / тоннель упал)
        return JSONResponse(
            status_code=502,
            content={"error": f"tutor-llm недоступен ({TUTOR_LLM_URL}): {exc}"},
        )
