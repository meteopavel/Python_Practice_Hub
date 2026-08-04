# -*- coding: utf-8 -*-
"""Тир B — HTTP-API попыток ученика: удаление одной попытки тьютором.

Эндпойнт ``DELETE /api/students/{student_id}/attempts/{attempt_id}``
(routes/students.py) — серверная половина механики feat.2: тьютор удаляет
любую попытку ученика (удачную или нет, в любом порядке). Статус
решённости — производное от Attempt.passed (task_status_map в _common.py:
'pass' если хоть одна попытка прошла), поэтому контракт такой:

  - 401 без сессии, 403 от ученика (эндпоинт тьюторский);
  - 404 если ученик или попытка не найдены / чужая;
  - 200 + {task_id, status} со свежим статусом задачи после удаления:
      * удалили последнюю удачную при наличии неудачных → 'fail';
      * удалили все попытки → status=null (индикатор исчезает);
      * удалили одну из нескольких удачных → остаётся 'pass'.

WS-реле второй половины (attempts_changed летит ученику) покрыто в
test_ws_live.py. Здесь — только HTTP-контракт и пересчёт статуса на бэке."""
from sqlalchemy.orm import sessionmaker

from webapp.core.models import Attempt


def _add_attempt(db, user_id, task_id, passed, code="x"):
    """Создать попытку напрямую в БД и вернуть её id (с commit)."""
    a = Attempt(user_id=user_id, task_id=task_id, code=code, passed=passed)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a.id


def _db(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


# --- Авторизация и валидация ------------------------------------------------

class TestDeleteAuth:
    def test_unauth_returns_401(self, client, student):
        r = client.delete(f"/api/students/{student.id}/attempts/1")
        assert r.status_code == 401

    def test_student_forbidden(self, student_client, student):
        # Эндпоинт тьюторский — ученику 403, даже если параметры корректны.
        r = student_client.delete(f"/api/students/{student.id}/attempts/1")
        assert r.status_code == 403

    def test_unknown_student_returns_404(self, tutor_client):
        r = tutor_client.delete("/api/students/99999/attempts/1")
        assert r.status_code == 404

    def test_unknown_attempt_returns_404(self, tutor_client, student):
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/99999")
        assert r.status_code == 404


# --- Пересчёт статуса при удалении ------------------------------------------

class TestDeleteStatusRecompute:
    def test_delete_last_pass_with_fail_remains_becomes_fail(self, tutor_client, student, engine):
        # pass + fail по одной задаче: удаляем pass → остаётся fail → 'fail'.
        db = _db(engine)
        try:
            fail_id = _add_attempt(db, student.id, task_id=5, passed=False)
            pass_id = _add_attempt(db, student.id, task_id=5, passed=True)
        finally:
            db.close()
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/{pass_id}")
        assert r.status_code == 200
        assert r.json() == {"task_id": 5, "status": "fail"}
        # fail-попытка на месте.
        db = _db(engine)
        try:
            assert db.query(Attempt).filter(Attempt.id == fail_id).one()
        finally:
            db.close()

    def test_delete_all_attempts_status_null(self, tutor_client, student, engine):
        # Удаляем последнюю попытку (pass) — других нет → status=null, индикатор
        # исчезает (как при монотонном pass в task_status_map).
        db = _db(engine)
        try:
            pass_id = _add_attempt(db, student.id, task_id=7, passed=True)
        finally:
            db.close()
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/{pass_id}")
        assert r.status_code == 200
        assert r.json() == {"task_id": 7, "status": None}

    def test_delete_one_of_many_pass_stays_pass(self, tutor_client, student, engine):
        # Две удачные: удаляем одну — задание остаётся решённым ('pass').
        db = _db(engine)
        try:
            p1 = _add_attempt(db, student.id, task_id=9, passed=True)
            p2 = _add_attempt(db, student.id, task_id=9, passed=True)
        finally:
            db.close()
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/{p1}")
        assert r.status_code == 200
        assert r.json() == {"task_id": 9, "status": "pass"}

    def test_delete_fail_when_pass_exists_stays_pass(self, tutor_client, student, engine):
        # pass + fail: удаляем fail — pass остаётся, статус по-прежнему 'pass'.
        db = _db(engine)
        try:
            fail_id = _add_attempt(db, student.id, task_id=11, passed=False)
            _add_attempt(db, student.id, task_id=11, passed=True)
        finally:
            db.close()
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/{fail_id}")
        assert r.status_code == 200
        assert r.json() == {"task_id": 11, "status": "pass"}

    def test_other_student_attempt_returns_404(self, tutor_client, student, tutor, engine):
        # Попытка чужого ученика (по student_id в URL нет такой попытки) → 404.
        # Защита от удаления попытки одного ученика через URL другого.
        db = _db(engine)
        try:
            # Создаём попытку от имени тьютора (как user_id) — она не принадлежит student.
            attempt_id = _add_attempt(db, tutor.id, task_id=3, passed=True)
        finally:
            db.close()
        r = tutor_client.delete(f"/api/students/{student.id}/attempts/{attempt_id}")
        assert r.status_code == 404


# --- id в ответе task_attempts (нужен фронту для DELETE) --------------------

class TestAttemptIdExposed:
    def test_attempts_list_contains_id(self, student_client, student, engine):
        # task_attempts (_common.py) должен отдавать id каждой попытки — без
        # него фронт не сможет вызвать DELETE /attempts/{id}.
        db = _db(engine)
        try:
            _add_attempt(db, student.id, task_id=13, passed=True, code="ok")
        finally:
            db.close()
        r = student_client.get("/api/attempts/mine/13")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert isinstance(data[0]["id"], int)
        assert data[0]["passed"] is True
