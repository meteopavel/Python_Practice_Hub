# -*- coding: utf-8 -*-
"""bug.9 — HTTP-API смены собственного пароля и политика минимальной длины.

Эндпоинт ``POST /api/me/password`` (routes/auth.py) — самостоятельная смена
своего пароля, доступная обеим ролям (раньше была только тьюторская смена
пароля ученику). Контракт:

  - 401 без сессии;
  - 400 «Неверный текущий пароль» — обязательная сверка старого пароля;
  - 400 если новый короче MIN_PASSWORD_LENGTH (8);
  - 200 + {"ok": true} — после смены логин старым паролем не проходит,
    новым — работает.

Политика длины (password_policy_error в core/auth.py) применяется и в
тьюторских роутах (создание ученика, смена пароля ученику) — здесь их
регресс-покрытие: короткий пароль → 400, ровно 8 символов — граница
прохода."""
from webapp.core.auth import MIN_PASSWORD_LENGTH

NEW_PASSWORD = "newpass-123"


class TestChangeOwnPassword:
    def test_unauth_returns_401(self, client, student):
        r = client.post("/api/me/password", json={"current_password": "password", "new_password": NEW_PASSWORD})
        assert r.status_code == 401

    def test_wrong_current_password_returns_400(self, student_client, student):
        r = student_client.post("/api/me/password", json={"current_password": "не-тот", "new_password": NEW_PASSWORD})
        assert r.status_code == 400
        assert "текущий" in r.json()["error"].lower()

    def test_short_new_password_returns_400(self, student_client, student):
        r = student_client.post("/api/me/password", json={"current_password": "password", "new_password": "short"})
        assert r.status_code == 400
        assert str(MIN_PASSWORD_LENGTH) in r.json()["error"]

    def test_success_old_password_stops_working(self, student_client, student, client):
        # Ученик (default-пароль фикстуры "password") меняет пароль на новый.
        r = student_client.post("/api/me/password", json={"current_password": "password", "new_password": NEW_PASSWORD})
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        # Старым паролем больше не зайти, новым — можно.
        old = client.post("/login", data={"username": student.username, "password": "password"}, follow_redirects=False)
        assert old.status_code == 303
        assert old.headers["location"].startswith("/login?error")
        new = client.post("/login", data={"username": student.username, "password": NEW_PASSWORD}, follow_redirects=False)
        assert new.status_code == 303
        assert new.headers["location"] == "/"

    def test_tutor_can_change_own_password_too(self, tutor_client, tutor, client):
        # Эндпоинт не тьюторский и не ученический — работает для любой роли.
        r = tutor_client.post("/api/me/password", json={"current_password": "password", "new_password": NEW_PASSWORD})
        assert r.status_code == 200
        new = client.post("/login", data={"username": tutor.username, "password": NEW_PASSWORD}, follow_redirects=False)
        assert new.status_code == 303
        assert new.headers["location"] == "/"

    def test_session_survives_password_change(self, student_client, student):
        # Сессия — подписанная cookie, от пароля не зависит: после смены
        # текущая сессия продолжает работать (решение зафиксировано в
        # docs/decisions.md, bug.9).
        r = student_client.post("/api/me/password", json={"current_password": "password", "new_password": NEW_PASSWORD})
        assert r.status_code == 200
        me = student_client.get("/api/me")
        assert me.status_code == 200
        assert me.json()["username"] == student.username


class TestPasswordPolicyInTutorRoutes:
    def test_create_student_short_password_returns_400(self, tutor_client):
        r = tutor_client.post("/api/students", json={"username": "newbie", "password": "short"})
        assert r.status_code == 400

    def test_create_student_exact_min_length_ok(self, tutor_client):
        # Граница: ровно 8 символов — проходит.
        r = tutor_client.post("/api/students", json={"username": "newbie", "password": "12345678"})
        assert r.status_code == 200

    def test_set_student_password_short_returns_400(self, tutor_client, student):
        r = tutor_client.post(f"/api/students/{student.id}/password", json={"password": "short"})
        assert r.status_code == 400

    def test_set_student_password_exact_min_length_ok(self, tutor_client, student):
        r = tutor_client.post(f"/api/students/{student.id}/password", json={"password": "12345678"})
        assert r.status_code == 200
