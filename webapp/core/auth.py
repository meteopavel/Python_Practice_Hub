# -*- coding: utf-8 -*-
"""Простая авторизация логин/пароль + сессия по подписанной cookie.
Ученики заводятся вручную (см. create_user.py) — самостоятельной регистрации нет."""
import bcrypt
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from webapp.core.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def current_user_id(request: Request) -> int | None:
    return request.session.get("user_id")


def current_user_role(request: Request) -> str | None:
    return request.session.get("role")


def unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"error": "Не авторизован"})


def forbidden() -> JSONResponse:
    return JSONResponse(status_code=403, content={"error": "Доступно только репетитору"})
