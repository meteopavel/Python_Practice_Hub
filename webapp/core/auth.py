# -*- coding: utf-8 -*-
"""Простая авторизация логин/пароль + сессия по подписанной cookie.
Ученики заводятся вручную (см. create_user.py) — самостоятельной регистрации нет."""
import bcrypt
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from webapp.core.models import User

# Единая политика для всех мест, где пароль задаётся или меняется:
# self-service смена, тьютор ученику, CLI create_user.py.
MIN_PASSWORD_LENGTH = 8


def password_policy_error(password: str) -> str | None:
    """Текст ошибки, если пароль не проходит политику (минимальная длина),
    иначе None."""
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов"
    return None


def hash_password(password: str) -> str:
    """bcrypt-хэш пароля (соль генерируется и хранится внутри хэша)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Сверка пароля с хэшем."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate(db: Session, username: str, password: str) -> User | None:
    """User по логину+паролю или None (не различаем «нет юзера» и «не тот
    пароль», чтобы не подсказывать перебор)."""
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def current_user_id(request: Request) -> int | None:
    """id пользователя из сессии или None (аноним)."""
    return request.session.get("user_id")


def current_user_role(request: Request) -> str | None:
    """Роль из сессии ('student'/'tutor') или None (аноним)."""
    return request.session.get("role")


def unauthorized() -> JSONResponse:
    """Стандартный 401 для API-роутов."""
    return JSONResponse(status_code=401, content={"error": "Не авторизован"})


def forbidden() -> JSONResponse:
    """Стандартный 403: роут только для репетитора."""
    return JSONResponse(status_code=403, content={"error": "Доступно только репетитору"})
