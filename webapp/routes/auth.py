# -*- coding: utf-8 -*-
"""Роуты авторизации: вход/выход, текущий пользователь, режим «посмотреть как
ученик» (имперсонация)."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from webapp.core.auth import authenticate, current_user_id, current_user_role, unauthorized
from webapp.core.db import get_db
from webapp.core.models import ROLE_STUDENT, ROLE_TUTOR, User
from webapp.routes._common import effective_identity
from webapp.config import templates

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate(db, username, password)
    if user is None:
        return RedirectResponse(url="/login?error=1", status_code=303)
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
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


@router.post("/tutor/student/{student_id}/impersonate")
def start_impersonation(student_id: int, request: Request, db: Session = Depends(get_db)):
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
    student_id = request.session.pop("impersonate_student_id", None)
    if student_id is not None:
        return RedirectResponse(url=f"/tutor/student/{student_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)
