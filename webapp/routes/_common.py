# -*- coding: utf-8 -*-
"""Общее для нескольких модулей роутов: эффективная личность (имперсонация),
агрегаты попыток, ответ подсказок и Pydantic-модели запросов, которые
переиспользуются между доменами (submit/run_free — у ученика и у тьютора)."""
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webapp.content.hints import available_levels, render_markdown
from webapp.core.auth import current_user_id, current_user_role
from webapp.core.models import ROLE_STUDENT, ROLE_TUTOR, Attempt, User


def effective_identity(request: Request, db: Session):
    """Для тьютора в режиме "посмотреть как ученик" подменяет личность только
    для student-facing данных (список заданий/свои попытки) — НЕ для
    авторизации, та остаётся на реальной роли из сессии."""
    real_role = current_user_role(request)
    impersonate_id = request.session.get("impersonate_student_id")
    if impersonate_id and real_role == ROLE_TUTOR:
        student = db.query(User).filter(User.id == impersonate_id, User.role == ROLE_STUDENT).first()
        if student is not None:
            return student.id, True, request.session.get("username"), student.username
    return current_user_id(request), False, None, request.session.get("username")


def task_status_map(db: Session, user_id: int) -> dict:
    """task_id -> 'pass'/'fail' по всей истории попыток пользователя — 'pass'
    если хоть одна попытка когда-либо прошла. Общий код для своей истории
    (эффективная личность) и истории конкретного ученика (вид тьютора)."""
    rows = db.query(Attempt.task_id, Attempt.passed).filter(Attempt.user_id == user_id).all()
    passed_by_task = {}
    for task_id, passed in rows:
        passed_by_task[task_id] = passed_by_task.get(task_id, False) or passed
    return {task_id: ("pass" if passed else "fail") for task_id, passed in passed_by_task.items()}


def task_attempts(db: Session, user_id: int, task_id: int) -> list:
    rows = (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id, Attempt.task_id == task_id)
        .order_by(Attempt.created_at.asc())
        .all()
    )
    return [
        {
            "passed": a.passed,
            "code": a.code,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


def hints_response(db: Session, user_id: int, task_id: int) -> dict:
    """Общий вид ответа с состоянием подсказок для ученика — используется и в
    GET, и в POST /reveal, чтобы контракт был единый. Контент рендерим в HTML
    только для revealed (ученик видит готовый текст, не сырой markdown)."""
    levels = available_levels(db, user_id, task_id)
    for item in levels:
        if item.get("status") == "revealed":
            item["content_html"] = render_markdown(item.get("content", ""))
            item.pop("content", None)
    return {"task_id": task_id, "levels": levels}


def require_student(db: Session, student_id: int):
    return db.query(User).filter(User.id == student_id, User.role == ROLE_STUDENT).first()


# --- Pydantic-модели запросов -----------------------------------------------
# SubmissionRequest / HintFreeRunRequest шарятся между учеником (submit,
# solve/run_free) и тьютором (hint/run, hint/run_free) — поэтому живут здесь.
class SubmissionRequest(BaseModel):
    task_id: int
    code: str


class HintFreeRunRequest(BaseModel):
    code: str
