# -*- coding: utf-8 -*-
"""Тир B — HTTP-API многоступенчатых подсказок.

Эндпойнт ``POST /api/hints/{task_id}/reveal`` (routes/hints_api.py:47) —
серверная половина раскрытия уровня учеником (WS-реле второй половины — в
test_ws_live.py). Контракт:
  - 401 без сессии;
  - 404 для задания без подсказок (HINTED_TASK_IDS = 1..100);
  - 400 для level ∉ {1,2,3};
  - 409 если уровень недоступен (предыдущий не раскрыт ИЛИ задержка не прошла);
  - 200 + обновлённое состояние для ready/revealed (идемпотентно).

Тайминг задержек (7 мин до 2-й, 15 мин до 3-й) в проде считается по ``SELECT
NOW()`` из БД; здесь ``content.hints._now`` мокается, чтобы проверять 409/200
детерминированно. has_hints/task_id выбран так: 81 — есть в HINTED_TASK_IDS и в
seed-данных, 101 — служебная скрытая задача, подсказок не имеет (→ 404)."""
from datetime import datetime, timedelta, timezone

import pytest

from webapp.content import hints
from webapp.core.models import HintReveal

HINTED_TASK = 81   # входит в HINTED_TASK_IDS (1..100)
NON_HINTED = 101   # вне HINTED_TASK_IDS → has_hints → False → 404


@pytest.fixture
def frozen_now(monkeypatch):
    """То же, что в test_hints_logic: фиксированное «сейчас» для can_reveal,
    который сам зовёт _now(db). Без этого тайминг-тесты зависели бы от реального
    хода часов.

    ВАЖНО: ``_now`` в проде возвращает naive-время из ``SELECT NOW()`` (MySQL
    отдаёт без зоны — см. докстринг hints.py:52-59), а ``revealed_at`` пишется
    через ``func.now()`` тоже naive. Чтобы сравнение ``now >= available_at`` в
    _level_state не падало на aware/naive-несовпадении, мок тоже отдаёт naive.

    Старт берём от реального ``datetime.utcnow()``, а НЕ от фиксированной даты:
    ``revealed_at`` ставит БД через ``server_default=func.now()`` (реальное
    сейчас), и ``_now`` должен быть с ним в одной шкале. Абсолютная дата теста
    неважна — проверяются относительные сдвиги через ``tick(minutes=...)``."""
    start = datetime.now(timezone.utc).replace(tzinfo=None)  # naive — как func.now() в проде

    class Clock:
        def __init__(self):
            self.value = start

        def tick(self, **kwargs):
            self.value += timedelta(**kwargs)

    clock = Clock()
    monkeypatch.setattr(hints, "_now", lambda db: clock.value)
    return clock


# --- Авторизация и валидация входа -------------------------------------------

class TestRevealAuthAndValidation:
    def test_unauth_returns_401(self, client):
        r = client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        assert r.status_code == 401

    def test_non_hinted_task_returns_404(self, student_client):
        r = student_client.post(f"/api/hints/{NON_HINTED}/reveal", json={"level": 1})
        assert r.status_code == 404

    def test_get_hints_non_hinted_returns_404(self, student_client):
        # GET /api/hints/{task_id} имеет тот же has_hints gate — проверяем и его.
        r = student_client.get(f"/api/hints/{NON_HINTED}")
        assert r.status_code == 404

    @pytest.mark.parametrize("bad_level", [0, 4, -1, 100])
    def test_invalid_level_returns_400(self, student_client, bad_level):
        r = student_client.post(
            f"/api/hints/{HINTED_TASK}/reveal", json={"level": bad_level}
        )
        assert r.status_code == 400


# --- Успешное раскрытие ------------------------------------------------------

class TestRevealSuccess:
    def test_reveal_level1_returns_state(self, student_client, student, engine, frozen_now):
        r = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        assert r.status_code == 200
        body = r.json()
        assert body["task_id"] == HINTED_TASK
        levels = {lvl["level"]: lvl for lvl in body["levels"]}
        assert levels[1]["status"] == "revealed"
        # revealed-уровень отдаёт отрендеренный HTML, сырой markdown убирается.
        assert "content_html" in levels[1]
        assert "content" not in levels[1]

    def test_reveal_persists_hint_reveal_row(self, student_client, student, engine, frozen_now):
        student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        from sqlalchemy.orm import sessionmaker
        db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        try:
            rows = db.query(HintReveal).filter_by(
                user_id=student.id, task_id=HINTED_TASK
            ).all()
            assert len(rows) == 1
            assert rows[0].level == 1
        finally:
            db.close()

    def test_double_reveal_is_idempotent(self, student_client, student, engine, frozen_now):
        # Повторный reveal того же уровня не создаёт дубль (UNIQUE) и не сдвигает
        # revealed_at — иначе можно было бы обнулить таймер следующего уровня.
        student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        second = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        assert second.status_code == 200
        from sqlalchemy.orm import sessionmaker
        db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        try:
            rows = db.query(HintReveal).filter_by(
                user_id=student.id, task_id=HINTED_TASK, level=1
            ).all()
            assert len(rows) == 1
        finally:
            db.close()


# --- Тайминг (gate 409) ------------------------------------------------------

class TestRevealTiming:
    def test_level2_locked_without_level1(self, student_client, frozen_now):
        # level 1 не раскрыт → 2-й locked → 409.
        r = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 2})
        assert r.status_code == 409

    def test_level2_waiting_before_7min(self, student_client, frozen_now):
        # Раскрываем 1-й, потом сразу лезем за 2-м — задержка 7 мин не прошла.
        student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        frozen_now.tick(minutes=6)  # < 7
        r = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 2})
        assert r.status_code == 409

    def test_level2_ready_after_7min(self, student_client, frozen_now):
        student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        frozen_now.tick(minutes=8)  # > 7
        r = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 2})
        assert r.status_code == 200

    def test_level3_chain_requires_both_previous(self, student_client, frozen_now):
        # 3-й требует раскрытого 2-го; 1-й один недостаточен.
        student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 1})
        frozen_now.tick(minutes=100)
        r = student_client.post(f"/api/hints/{HINTED_TASK}/reveal", json={"level": 3})
        assert r.status_code == 409


# --- GET /api/hints (состояние) ----------------------------------------------

class TestGetHints:
    def test_all_locked_initially(self, student_client, frozen_now):
        # До раскрытия: level 1 — ready, 2/3 — locked. Контент не отдаётся.
        r = student_client.get(f"/api/hints/{HINTED_TASK}")
        assert r.status_code == 200
        levels = {lvl["level"]: lvl for lvl in r.json()["levels"]}
        assert levels[1]["status"] == "ready"
        assert levels[2]["status"] == "locked"
        assert levels[3]["status"] == "locked"
        # Контент не должен утекать ни в каком виде для нераскрытых уровней.
        for lvl in levels.values():
            assert "content" not in lvl
            assert "content_html" not in lvl

    def test_unauth_returns_401(self, client):
        r = client.get(f"/api/hints/{HINTED_TASK}")
        assert r.status_code == 401
