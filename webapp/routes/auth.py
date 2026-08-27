# -*- coding: utf-8 -*-
"""Роуты авторизации: вход/выход, текущий пользователь, режим «посмотреть как
ученик» (имперсонация)."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webapp.core.auth import (
    authenticate,
    current_user_id,
    current_user_role,
    hash_password,
    password_policy_error,
    unauthorized,
    verify_password,
)
from webapp.core.db import get_db
from webapp.core.models import ROLE_STUDENT, ROLE_TUTOR, User
from webapp.routes._common import effective_identity
from webapp.config import templates

router = APIRouter()


class ChangePasswordRequest(BaseModel):
    """Смена собственного пароля: подтверждение текущим + новый."""

    current_password: str
    new_password: str


@router.get("/login")
def login_page(request: Request):
    """Страница входа (форма логин/пароль)."""
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Вход по логину/паролю: при успехе user_id/username/role пишутся в
    подписанную сессионную cookie; при неудаче — назад на /login?error=1."""
    user = authenticate(db, username, password)
    if user is None:
        return RedirectResponse(url="/login?error=1", status_code=303)
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    """Выход: сессия очищается целиком (включая флаг имперсонации)."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    """Текущий пользователь для фронта: эффективные имя/роль (при
    имперсонации — ученик), факт подмены и реальное имя тьютора."""
    if current_user_id(request) is None:
        return unauthorized()
    user_id, impersonating, real_username, username = effective_identity(request, db)
    return {
        "id": user_id,
        "username": username,
        "role": ROLE_STUDENT if impersonating else request.session.get("role"),
        "impersonating": impersonating,
        "real_username": real_username,
    }


@router.post("/api/me/password")
def change_own_password(payload: ChangePasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Смена собственного пароля — доступна любой роли (и тьютору, и ученику).
    Требует текущий пароль, новый проходит политику минимальной длины
    (password_policy_error). Другие активные сессии пользователя при этом не
    инвалидируются: сессия — stateless подписанная cookie, от пароля не
    зависит (см. docs/decisions.md, bug.9)."""
    user_id = current_user_id(request)
    if user_id is None:
        return unauthorized()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return unauthorized()
    if not verify_password(payload.current_password, user.password_hash):
        return JSONResponse(status_code=400, content={"error": "Неверный текущий пароль"})
    if (err := password_policy_error(payload.new_password)) is not None:
        return JSONResponse(status_code=400, content={"error": err})
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


@router.post("/tutor/student/{student_id}/impersonate")
def start_impersonation(student_id: int, request: Request, db: Session = Depends(get_db)):
    """Войти в режим «посмотреть как ученик»: в сессию пишется
    impersonate_student_id, student-facing данные показываются от лица
    ученика; авторизация тьюторских роутов остаётся на реальной роли."""
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    student = db.query(User).filter(User.id == student_id, User.role == ROLE_STUDENT).first()
    if student is not None:
        # Эффективная личность только для student-facing данных (см.
        # effective_identity) — авторизация тьюторских роутов идёт по
        # реальной роли из сессии и этим флагом не затрагивается.
        request.session["impersonate_student_id"] = student.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/impersonate/stop")
def stop_impersonation(request: Request):
    """Выйти из режима имперсонации — возврат на страницу этого ученика."""
    student_id = request.session.pop("impersonate_student_id", None)
    if student_id is not None:
        return RedirectResponse(url=f"/tutor/student/{student_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)
