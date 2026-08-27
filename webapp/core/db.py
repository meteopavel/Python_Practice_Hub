# -*- coding: utf-8 -*-
"""Подключение к БД: движок + фабрика сессий SQLAlchemy."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local.db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Зависимость FastAPI: своя сессия на каждый запрос, гарантированно
    закрывается в finally."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
