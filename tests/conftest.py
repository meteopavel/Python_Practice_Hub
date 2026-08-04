# -*- coding: utf-8 -*-
"""Общий fixtures-слой для тестов.

Ключевые подводные камни, которые здесь решаются:

1. ``webapp.config`` падает RuntimeError на импорте без ``SESSION_SECRET`` —
   поэтому env выставляем НА ВЕРХНЕМ УРОВНЕ модуля, до первого ``import webapp``.
2. ``webapp.core.db`` создаёт engine на импорте из ``DATABASE_URL``. Чтобы тесты
   шли на in-memory SQLite, переменную тоже задаём заранее. А поскольку Starlette
   TestClient крутит ASGI-приложение в отдельном потоке, обычный
   ``sqlite:///:memory:`` дал бы каждому потоку свою пустую БД — поэтому
   используем ``StaticPool`` с одним шаренным соединением.
3. ``get_db`` берёт ``SessionLocal`` из ``webapp.core.db`` на момент ОПРЕДЕЛЕНИЯ
   функции. Поскольку мы подменяем ``SessionLocal`` прямо в модуле ``db`` (а не
   через ``app.dependency_overrides``), существующий ``get_db`` подхватывает
   тестовую фабрику без дополнительной настройки.
4. ``webapp.core.realtime.rooms`` — глобальный in-memory dict. Если его не
   чистить между тестами, один WebSocket-тест у другого увидит чужие сокеты/
   «последний код». Чистим автопустой фикстурой перед каждым тестом.
"""
import os

os.environ.setdefault("SESSION_SECRET", "test-session-secret-not-for-prod")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402  (env должен стоять до этого импорта webapp)
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from webapp.core import db as db_module  # noqa: E402
from webapp.core.models import Base, ROLE_STUDENT, ROLE_TUTOR, User  # noqa: E402
from webapp.core.realtime import rooms  # noqa: E402


# --- Тестовая БД -------------------------------------------------------------

@pytest.fixture
def engine():
    """Свежий in-memory SQLite engine на каждый тест.

    StaticPool держит ровно одно соединение на жизнь engine, так что все потоки
    (включая поток Starlette TestClient) видят одни и те же таблицы и данные.
    Без него ``:memory:`` создавало бы отдельную БД на каждое соединение."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    # Подменяем фабрику сессий в самом модуле db, чтобы существующий get_db()
    # (через Depends(get_db)) уже раздавал тестовые сессии без override'ов.
    _original_session_local = db_module.SessionLocal
    db_module.SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    try:
        yield _engine
    finally:
        db_module.SessionLocal = _original_session_local
        Base.metadata.drop_all(bind=_engine)
        _engine.dispose()


@pytest.fixture(autouse=True)
def _reset_realtime_rooms():
    """Чистим глобальные live-комнаты перед каждым тестом, иначе WS-тесты
    наследуют чужие сокеты и last_student_code от предыдущих прогонов."""
    rooms.clear()
    yield
    rooms.clear()


# --- Пользователи ------------------------------------------------------------

def _make_user(db, username, role, password="password"):
    from webapp.core.auth import hash_password
    user = User(username=username, role=role, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student(engine):
    """Ученик в БД (возвращает ORM-объект)."""
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        return _make_user(db, "student1", ROLE_STUDENT)
    finally:
        db.close()


@pytest.fixture
def tutor(engine):
    """Тьютор в БД (возвращает ORM-объект)."""
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        return _make_user(db, "tutor1", ROLE_TUTOR)
    finally:
        db.close()


# --- HTTP / WebSocket клиенты ------------------------------------------------

@pytest.fixture
def app(engine):
    # Импортируем здесь (а не на верхнем уровне), чтобы фикстура engine успела
    # подменить SessionLocal ДО того, как роуты возьмут get_db. app создаётся
    # один раз — при первом импорте webapp.main; этого достаточно, т.к. get_db
    # читает SessionLocal из модуля динамически при каждом вызове.
    from webapp.main import app as _app
    return _app


@pytest.fixture
def client(app):
    """Анонимный TestClient (без сессии)."""
    with TestClient(app) as c:
        yield c


def _login(client, username, password="password"):
    """Честный логин через POST /login — ставит session-cookie, которую
    TestClient дальше пробрасывает и в HTTP, и в websocket_connect."""
    resp = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert resp.status_code == 303, f"Логин не удался: {resp.status_code} {resp.text}"


@pytest.fixture
def student_client(app, student):
    """TestClient, залогиненный как ученик ``student``."""
    with TestClient(app) as c:
        _login(c, student.username)
        yield c


@pytest.fixture
def tutor_client(app, student, tutor):
    """TestClient, залогиненный как тьютор ``tutor``.

    Зависит от ``student``, чтобы фиксировать порядок создания (ученик раньше
    тьютора) — это не функционально обязательно, но даёт детерминизм id: у
    ученика гарантированно меньший id, чем у тьютора, что удобно в ассертах."""
    with TestClient(app) as c:
        _login(c, tutor.username)
        yield c
