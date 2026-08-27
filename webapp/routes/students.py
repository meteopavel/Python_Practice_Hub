# -*- coding: utf-8 -*-
"""Роуты тьютора по ученикам: список, создание, смена пароля, попытки и
состояние подсказок конкретного ученика (мониторинг + сброс)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from webapp.core.auth import (
    current_user_id,
    current_user_role,
    forbidden,
    hash_password,
    password_policy_error,
    unauthorized,
)
from webapp.core.db import get_db
from webapp.core.models import ROLE_STUDENT, Attempt, User
from webapp.content.hints import LEVELS, has_hints, reset_reveal_cascade
from webapp.routes._common import hints_response, require_student, task_attempts, task_status_map

router = APIRouter()


class CreateStudentRequest(BaseModel):
    """Завести ученика: логин + стартовый пароль."""

    username: str
    password: str


class SetPasswordRequest(BaseModel):
    """Тьютор задаёт ученику новый пароль (старый не нужен — это тьютор)."""

    password: str


class HintResetRequest(BaseModel):
    """Тьютор сбрасывает раскрытый уровень подсказки ученика (level — 1|2|3).
    Сбрасывается сам уровень и все раскрытые уровни выше него по цепочке."""
    level: int


def _require_tutor(request: Request):
    """Возвращает JSONResponse-ошибку (401/403), если запрос не от тьютора,
    иначе None. Каждый роут ниже начинает с `if (err := _require_tutor(...)): return err`."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != "tutor":
        return forbidden()
    return None


@router.get("/api/students")
def list_students(request: Request, db: Session = Depends(get_db)):
    """Все ученики тьютора + агрегаты по попыткам (сколько всего, когда
    последняя) — одним запросом, без N+1."""
    if (err := _require_tutor(request)) is not None:
        return err
    students = db.query(User).filter(User.role == ROLE_STUDENT).order_by(User.username).all()
    # Агрегаты по попыткам — одним запросом (count + max(created_at) с группировкой
    # по user_id), не N+1 (раньше было 2 запроса на каждого студента в цикле).
    student_ids = [s.id for s in students]
    agg_rows = (
        db.query(Attempt.user_id.label("uid"), func.count(Attempt.id).label("cnt"), func.max(Attempt.created_at).label("last"))
        .filter(Attempt.user_id.in_(student_ids))
        .group_by(Attempt.user_id)
        .all()
    ) if student_ids else []
    agg = {row.uid: (row.cnt, row.last) for row in agg_rows}
    result = []
    for student in students:
        cnt, last = agg.get(student.id, (0, None))
        result.append({
            "id": student.id,
            "username": student.username,
            "attempts_count": cnt,
            "last_attempt_at": last.isoformat() if last else None,
        })
    return result


@router.post("/api/students")
def create_student(payload: CreateStudentRequest, request: Request, db: Session = Depends(get_db)):
    """Создать ученика: логин уникален, пароль проходит политику, в БД —
    bcrypt-хэш."""
    if (err := _require_tutor(request)) is not None:
        return err
    username = payload.username.strip()
    if not username:
        return JSONResponse(status_code=400, content={"error": "Логин не должен быть пустым"})
    if (err := password_policy_error(payload.password)) is not None:
        return JSONResponse(status_code=400, content={"error": err})
    if db.query(User).filter(User.username == username).first() is not None:
        return JSONResponse(status_code=400, content={"error": f"Логин «{username}» уже занят"})
    student = User(username=username, password_hash=hash_password(payload.password), role=ROLE_STUDENT)
    db.add(student)
    db.commit()
    return {"id": student.id, "username": student.username}


@router.post("/api/students/{student_id}/password")
def set_student_password(student_id: int, payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Сменить пароль ученика (роль всегда student; политика проверяется)."""
    if (err := _require_tutor(request)) is not None:
        return err
    if (err := password_policy_error(payload.password)) is not None:
        return JSONResponse(status_code=400, content={"error": err})
    student = require_student(db, student_id)
    if student is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    student.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


@router.get("/api/students/{student_id}/attempts/status")
def student_task_status(student_id: int, request: Request, db: Session = Depends(get_db)):
    """Статус всех заданий ученика ('pass'/'fail') — для монитора тьютора."""
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    return task_status_map(db, student_id)


@router.get("/api/students/{student_id}/attempts/{task_id}")
def student_task_attempts(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    """Все попытки ученика по одному заданию: код, passed, время."""
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    return task_attempts(db, student_id, task_id)


@router.get("/api/students/{student_id}/hints/{task_id}")
def student_hints(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    """Состояние подсказок задания для конкретного ученика — глазами тьютора
    (мониторинг прогресса раскрытия, без reveal-кнопок). Та же логика, что у
    ученического GET /api/hints, но user_id берётся явно из student_id, а не
    из effective_identity. Контент отдаётся для revealed (тьютор видит, что
    именно ученик уже прочитал)."""
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    return hints_response(db, student_id, task_id)


@router.post("/api/students/{student_id}/hints/{task_id}/reset")
def reset_student_hint(student_id: int, task_id: int, payload: HintResetRequest, request: Request, db: Session = Depends(get_db)):
    """Тьютор сбрасывает раскрытый уровень подсказки ученика — ученик снова
    увидит его закрытым (как будто не открывал). Сбрасывается сам уровень и
    каскадно все раскрытые уровни выше, чтобы не получить невозможное
    состояние «старший открыт, а его якорь закрыт». Действие необратимо:
    истории раскрытия в БД нет. Возвращает свежее состояние подсказок."""
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if payload.level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Неверный уровень подсказки"})
    reset_reveal_cascade(db, student_id, task_id, payload.level)
    return hints_response(db, student_id, task_id)


@router.delete("/api/students/{student_id}/attempts/{attempt_id}")
def delete_student_attempt(student_id: int, attempt_id: int, request: Request, db: Session = Depends(get_db)):
    """Тьютор удаляет одну попытку ученика — удачную или нет, в любом порядке.
    Статус решённости — производное от Attempt.passed (task_status_map в
    _common.py: 'pass' если хоть одна попытка прошла), поэтому удаление
    последней удачной попытки делает задание снова нерешённым ('fail', если
    остались неудачные), а удаление всех — возвращает в начальное состояние
    (статус пропадает, индикатор исчезает). Возвращает свежий статус задачи,
    чтобы фронт сразу перекрасил точку и перезагрузил список попыток."""
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id, Attempt.user_id == student_id).first()
    if attempt is None:
        return JSONResponse(status_code=404, content={"error": "Попытка не найдена"})
    task_id = attempt.task_id
    db.delete(attempt)
    db.commit()
    status_map = task_status_map(db, student_id)
    return {"task_id": task_id, "status": status_map.get(task_id)}
