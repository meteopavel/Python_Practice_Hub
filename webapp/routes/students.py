# -*- coding: utf-8 -*-
"""Роуты тьютора по ученикам: список, создание, смена пароля, попытки и
состояние подсказок конкретного ученика (мониторинг + сброс)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webapp.core.auth import current_user_id, current_user_role, forbidden, hash_password, unauthorized
from webapp.core.db import get_db
from webapp.core.models import ROLE_STUDENT, Attempt, User
from webapp.content.hints import LEVELS, has_hints, reset_reveal_cascade
from webapp.routes._common import hints_response, require_student, task_attempts, task_status_map

router = APIRouter()


class CreateStudentRequest(BaseModel):
    username: str
    password: str


class SetPasswordRequest(BaseModel):
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
    if (err := _require_tutor(request)) is not None:
        return err
    students = db.query(User).filter(User.role == ROLE_STUDENT).order_by(User.username).all()
    result = []
    for student in students:
        last_attempt = (
            db.query(Attempt)
            .filter(Attempt.user_id == student.id)
            .order_by(Attempt.created_at.desc())
            .first()
        )
        attempts_count = db.query(Attempt).filter(Attempt.user_id == student.id).count()
        result.append({
            "id": student.id,
            "username": student.username,
            "attempts_count": attempts_count,
            "last_attempt_at": last_attempt.created_at.isoformat() if last_attempt and last_attempt.created_at else None,
        })
    return result


@router.post("/api/students")
def create_student(payload: CreateStudentRequest, request: Request, db: Session = Depends(get_db)):
    if (err := _require_tutor(request)) is not None:
        return err
    username = payload.username.strip()
    if not username or not payload.password:
        return JSONResponse(status_code=400, content={"error": "Логин и пароль не должны быть пустыми"})
    if db.query(User).filter(User.username == username).first() is not None:
        return JSONResponse(status_code=400, content={"error": f"Логин «{username}» уже занят"})
    student = User(username=username, password_hash=hash_password(payload.password), role=ROLE_STUDENT)
    db.add(student)
    db.commit()
    return {"id": student.id, "username": student.username}


@router.post("/api/students/{student_id}/password")
def set_student_password(student_id: int, payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    if (err := _require_tutor(request)) is not None:
        return err
    if not payload.password:
        return JSONResponse(status_code=400, content={"error": "Пароль не должен быть пустым"})
    student = require_student(db, student_id)
    if student is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    student.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


@router.get("/api/students/{student_id}/attempts/status")
def student_task_status(student_id: int, request: Request, db: Session = Depends(get_db)):
    if (err := _require_tutor(request)) is not None:
        return err
    if require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    return task_status_map(db, student_id)


@router.get("/api/students/{student_id}/attempts/{task_id}")
def student_task_attempts(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
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
