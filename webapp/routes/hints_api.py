# -*- coding: utf-8 -*-
"""Роуты многоступенчатых подсказок: ученические (GET/reveal) и админка
тьютора (редактирование текстов уровней). Логика тайминга и доступа — в
content/hints.py, здесь только авторизация и валидация task_id/level."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webapp.core.auth import current_user_id, current_user_role, forbidden, unauthorized
from webapp.core.db import get_db
from webapp.core.models import Hint
from webapp.content.hints import HINTED_TASK_IDS, LEVELS, can_reveal, has_hints, record_reveal
from webapp.grading.bot_bridge import TASKS
from webapp.routes._common import effective_identity, hints_response

router = APIRouter()


class HintRevealRequest(BaseModel):
    """Ученик запрашивает раскрытие уровня подсказки. level — 1|2|3."""
    level: int


class HintContentRequest(BaseModel):
    """Тьютор сохраняет текст уровня (markdown)."""
    content: str = ""


@router.get("/api/hints/{task_id}")
def get_hints(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Состояние подсказок задания для ученика: по уровню — статус (locked /
    waiting / ready / revealed), для revealed — отрендеренный HTML контента,
    для waiting — available_at (когда станет ready, сервер считает тайминг).

    Контент отдаётся только для уже раскрытых уровней; для waiting сервер
    остаётся источником правды о готовности — фронт по обнулении таймера
    перезапрашивает это состояние."""
    if current_user_id(request) is None:
        return unauthorized()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    user_id, _, _, _ = effective_identity(request, db)
    return hints_response(db, user_id, task_id)


@router.post("/api/hints/{task_id}/reveal")
def reveal_hint(task_id: int, payload: HintRevealRequest, request: Request, db: Session = Depends(get_db)):
    """Ученик раскрывает уровень подсказки. Сервер решает, можно ли сейчас
    раскрыть (предыдущий уровень раскрыт И его задержка прошла), иначе 409.
    Повторный запрос на уже раскрытый уровень — идемпотентен (не создаёт
    дубль и не сдвигает revealed_at)."""
    if current_user_id(request) is None:
        return unauthorized()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if payload.level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Уровень должен быть 1, 2 или 3"})
    user_id, _, _, _ = effective_identity(request, db)
    if not can_reveal(db, user_id, task_id, payload.level):
        return JSONResponse(
            status_code=409,
            content={"error": "Уровень пока недоступен — подождите или раскройте предыдущую ступень"},
        )
    record_reveal(db, user_id, task_id, payload.level)
    return hints_response(db, user_id, task_id)


# --- Админка подсказок (только тьютор) -------------------------------------


def _require_tutor(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != "tutor":
        return forbidden()
    return None


@router.get("/api/admin/hints")
def admin_list_hints(request: Request, task_id: int, db: Session = Depends(get_db)):
    """Текст всех трёх уровней задания (включая пустые) — для редактора
    тьютора. Отдаём сырой markdown, не HTML: в форме его правят как текст."""
    if (err := _require_tutor(request)) is not None:
        return err
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    rows = db.query(Hint).filter(Hint.task_id == task_id).all()
    by_level = {r.level: r.content for r in rows}
    return {"task_id": task_id, "levels": [{"level": lvl, "content": by_level.get(lvl, "")} for lvl in LEVELS]}


@router.put("/api/admin/hints/{task_id}/{level}")
def admin_save_hint(task_id: int, level: int, payload: HintContentRequest, request: Request, db: Session = Depends(get_db)):
    """Сохранить (upsert) текст уровня подсказки. Контент — markdown,
    правит тьютор. Создание/обновление одной записью на (task_id, level)."""
    if (err := _require_tutor(request)) is not None:
        return err
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Уровень должен быть 1, 2 или 3"})
    row = db.query(Hint).filter(Hint.task_id == task_id, Hint.level == level).first()
    if row is None:
        db.add(Hint(task_id=task_id, level=level, content=payload.content))
    else:
        row.content = payload.content
    db.commit()
    return {"task_id": task_id, "level": level, "content": payload.content}


# Список заданий с подсказками — для селектора в админке (номер + описание,
# чтобы тьютору было понятно, какое задание он правит).
@router.get("/api/admin/hints/tasks")
def admin_hinted_tasks(request: Request):
    if (err := _require_tutor(request)) is not None:
        return err
    return [
        {"id": task_id, "description": TASKS[task_id]["description"]}
        for task_id in sorted(HINTED_TASK_IDS)
    ]
