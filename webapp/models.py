# -*- coding: utf-8 -*-
"""Модели: пользователи (ученики и репетитор, заводятся вручную) и попытки решения."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from db import Base

ROLE_STUDENT = "student"
ROLE_TUTOR = "tutor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), nullable=False, default=ROLE_STUDENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, nullable=False, index=True)
    code = Column(Text, nullable=False)
    passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# --- Многоступенчатые подсказки (задания 81..100) ---------------------------
# Hint — курированный контент (правит тьютор через админку). Одна запись на
# уровень (1|2|3) на задание.
# HintReveal — серверные отметки времени раскрытия уровней учеником. На них
# считается тайминг «7 минут до 2-й ступени, 15 минут до 3-й»: клиентскому
# таймеру верить нельзя (часы на устройстве ученика тривиально подменить),
# поэтому «когда уровень стал доступен» определяет только сервер по
# revealed_at предыдущего уровня.


class Hint(Base):
    __tablename__ = "hints"
    __table_args__ = (UniqueConstraint("task_id", "level", name="uq_hints_task_level"),)

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False, index=True)
    level = Column(SmallInteger, nullable=False)  # 1 | 2 | 3
    content = Column(Text, nullable=False, default="")  # markdown
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HintReveal(Base):
    __tablename__ = "hint_reveals"
    __table_args__ = (UniqueConstraint("user_id", "task_id", "level", name="uq_hint_reveals_user_task_level"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, nullable=False, index=True)
    level = Column(SmallInteger, nullable=False)  # 1 | 2 | 3
    revealed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
