# -*- coding: utf-8 -*-
"""Тир C — WebSocket live-сессия тьютор↔ученик. Ядро q.2 и bug.3.

Эндпойнт ``WS /ws/session/{student_id}`` (routes/ws.py) — мультиплексор:
живой код, подсказки, результаты проверок, сигналинг звонка. Здесь покрываем
именно live-релье (без WebRTC/звонка) — то, ради чего затевались тесты:
«ученик открыл подсказку → тьютор видит это сразу, без F5».

Три группы:
  - авторизация WS (4401 без сессии, 4403 студент в чужую комнату);
  - рестейты при подключении (тьютор получает последний код/подсказку/статус);
  - live-реле по типам сообщений в обе стороны — главный материал.

Четвёртая группа — ссылка дозвона офлайн-ученику (feat.9): pending живёт в
комнате, доставка при подключении, отзыв отменой или принятием.

Механика: открываем ДВА одновременных WS-соединения к одной комнате (студент +
тьютор) через два TestClient с разными session-cookie. ``live_room`` выпивает
шумные рестейты при подключении, так что дальше обмен идёт чисто: отправил →
получил ровно одно сообщение. Без браузера, детерминированно.
"""
from contextlib import contextmanager

import pytest
from starlette.websockets import WebSocketDisconnect

from webapp.core.models import ROLE_STUDENT, User
from webapp.core.auth import hash_password


# --- Вспомогательное ---------------------------------------------------------

def _drain(ws, n):
    """Прочитать и выбросить ``n`` сообщений из WS. Нужно, чтобы убрать
    рестейты, которые сервер шлёт при подключении (student_code/tutor_hint/
    *_status) — иначе первый receive_json в тесте перехватит рестейт вместо
    проверяемого live-сообщения. Число сообщений известно точно из ws.py."""
    for _ in range(n):
        ws.receive_json()


@contextmanager
def live_room(student_client, tutor_client, student_id):
    """Поднимает live-комнату: тьютор + студент на связи, рестейты выпиты.

    Порядок подключения — тьютор ПЕРВЫМ (до студента). Так при входе тьютора
    студент ещё офлайн и никакие сообщения студенту не уходят; проще считать
    рестейты. Из ws.py:
      - тьютор при подключении получает 3: student_code, tutor_hint,
        student_status(online=False);
      - студент при подключении получает 2: tutor_status(online=True),
        tutor_hint;
      - при подключении студента каждому тьютору уходит 1: student_status
        (online=True).
    После входа в yield оба сокета чисты и готовы к обмену."""
    with tutor_client.websocket_connect(f"/ws/session/{student_id}") as tutor_ws:
        _drain(tutor_ws, 3)  # student_code, tutor_hint, student_status(online=False)
        with student_client.websocket_connect(f"/ws/session/{student_id}") as student_ws:
            _drain(student_ws, 2)  # tutor_status(online=True), tutor_hint
            _drain(tutor_ws, 1)    # student_status(online=True)
            yield student_ws, tutor_ws


# --- Авторизация WS ----------------------------------------------------------

class TestWsAuth:
    def test_unauth_closes_4401(self, app, client):
        # Без сессии сервер закрывает сокет кодом 4401 (ws.py:19-21), не accept'я.
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/session/1") as ws:
                ws.receive_json()
        assert exc.value.code == 4401

    def test_student_into_other_room_closes_4403(self, app, engine, student_client, student):
        # Студент не может подключиться к комнате ДРУГОГО ученика (ws.py:22-24).
        # Создаём второго студента и пробуем зайти в его комнату от первого.
        from sqlalchemy.orm import sessionmaker
        db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        try:
            other = User(username="student2", role=ROLE_STUDENT,
                         password_hash=hash_password("password"))
            db.add(other)
            db.commit()
            db.refresh(other)
            other_id = other.id
        finally:
            db.close()

        with pytest.raises(WebSocketDisconnect) as exc:
            with student_client.websocket_connect(f"/ws/session/{other_id}") as ws:
                ws.receive_json()
        assert exc.value.code == 4403

    def test_student_into_own_room_accepted(self, app, student_client, student):
        # Контрпроверка: студент в свою комнату проходит — receive получает
        # начальные рестейты (tutor_status + tutor_hint), без disconnect.
        with student_client.websocket_connect(f"/ws/session/{student.id}") as ws:
            msg1 = ws.receive_json()
            msg2 = ws.receive_json()
            assert {msg1["type"], msg2["type"]} == {"tutor_status", "tutor_hint"}


# --- Рестейты при подключении ------------------------------------------------

class TestWsRestate:
    def test_tutor_receives_last_student_code(self, app, student_client, tutor_client, student):
        # Если ученик уже печатал (last_student_code заполнен), новый тьютор при
        # подключении должен получить этот код — а не пустую строку.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            # Студент печатает → тьютор получает student_code live.
            student_ws.send_json({"type": "student_code", "code": "x = 42", "task_id": 7})
            msg = tutor_ws.receive_json()
            assert msg == {"type": "student_code", "code": "x = 42", "task_id": 7}

        # Теперь открываем НОВОГО тьютора поверх той же комнаты — он должен
        # получить сохранённый last_student_code рестейтом.
        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as new_tutor:
            restate = new_tutor.receive_json()  # student_code
            assert restate["type"] == "student_code"
            assert restate["code"] == "x = 42"
            assert restate["task_id"] == 7

    def test_tutor_receives_tutor_hint_restate(self, app, student_client, tutor_client, student):
        # last_tutor_hint тоже хранится в комнате и отдаётся переподключившемуся
        # тьютору (и студенту при входе) — чтобы не потерять набранный текст.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "tutor_hint", "code": "подсказка!"})
            echoed = student_ws.receive_json()
            assert echoed == {"type": "tutor_hint", "code": "подсказка!"}

        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as new_tutor:
            new_tutor.receive_json()  # student_code (пустой)
            hint_restate = new_tutor.receive_json()  # tutor_hint
            assert hint_restate == {"type": "tutor_hint", "code": "подсказка!"}


# --- Live-реле student → tutor ----------------------------------------------

class TestStudentToTutorRelay:
    """Сообщения, которые идут только от ученика к тьютору (однонаправленные).
    Это ядро bug.3: тьютор видит действия ученика без F5."""

    def test_hint_revealed_relayed_to_tutor(self, app, student_client, tutor_client, student):
        # ⭐ Главный кейс q.2/bug.3: ученик раскрыл ступень подсказки — тьютор
        # получает hint_revealed немедленно и перерисовывает панель без F5.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            student_ws.send_json({"type": "hint_revealed", "task_id": 81, "level": 2})
            msg = tutor_ws.receive_json()
            assert msg == {"type": "hint_revealed", "task_id": 81, "level": 2}

    def test_submit_result_relayed_to_tutor(self, app, student_client, tutor_client, student):
        # Ученик нажал «Проверить» — тьютор сразу видит результат попытки, а не
        # только когда сам откроет «Попытки ученика» (bug.3: индикатор/точки).
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            student_ws.send_json({
                "type": "submit_result", "task_id": 5,
                "result": {"all_passed": True, "passed": 3, "total": 3},
            })
            msg = tutor_ws.receive_json()
            assert msg["type"] == "submit_result"
            assert msg["task_id"] == 5
            assert msg["result"]["all_passed"] is True

    def test_student_code_relayed_and_persisted(self, app, student_client, tutor_client, student):
        # Живой код: ученик печатает — тьютор видит обновление в реальном
        # времени. Сообщение без спец-типа (просто code/task_id) идёт по
        # дефолтной ветке и сохраняется в last_student_code комнаты.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            student_ws.send_json({"type": "student_code", "code": "print('hi')", "task_id": 1})
            msg = tutor_ws.receive_json()
            assert msg["type"] == "student_code"
            assert msg["code"] == "print('hi')"
            assert msg["task_id"] == 1


# --- Live-реле tutor → student ----------------------------------------------

class TestTutorToStudentRelay:
    """Сообщения от тьютора к ученику."""

    def test_tutor_hint_relayed_to_student(self, app, student_client, tutor_client, student):
        # Тьютор пишет в окне подсказки — ученик видит текст live.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "tutor_hint", "code": "исправь отступ"})
            msg = student_ws.receive_json()
            assert msg == {"type": "tutor_hint", "code": "исправь отступ"}

    def test_attempts_changed_relayed_to_student(self, app, student_client, tutor_client, student):
        # feat.2: тьютор удалил попытку ученика — статус мог измениться (pass→fail
        # или вовсе пропасть). Ученик видит это live: сообщение несёт свежий
        # статус, чтобы сразу перекрасить точку/индикатор.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "attempts_changed", "task_id": 12, "status": None})
            msg = student_ws.receive_json()
            assert msg == {"type": "attempts_changed", "task_id": 12, "status": None}

    def test_hint_visibility_relayed_to_student(self, app, student_client, tutor_client, student):
        # Тьютор открывает/закрывает подсказку «замком» — статус летит ученику.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "hint_visibility", "mode": "open"})
            msg = student_ws.receive_json()
            assert msg == {"type": "hint_visibility", "mode": "open"}

    def test_tutor_edit_code_relayed_to_student(self, app, student_client, tutor_client, student):
        # Тьютор правит код ученика напрямую (по кнопке) — применяется у ученика.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "tutor_edit_code", "code": "y = 1"})
            msg = student_ws.receive_json()
            assert msg == {"type": "tutor_edit_code", "code": "y = 1"}


# --- Направленные гейты ------------------------------------------------------

class TestDirectionGates:
    """Часть сообщений привязана к роли: attempts_changed — только от тьютора,
    hint_revealed/submit_result — только от ученика. Сообщение «не от той
    стороны» не ретранслируется (continue без send). Проверяем фильтрацию без
    таймаутов: шлём «неправильное» сообщение, затем валидное — и убеждаемся, что
    получатель видит только валидное (неправильное отфильтровалось)."""

    def test_attempts_changed_from_student_is_dropped(self, app, student_client, tutor_client, student):
        # attempts_changed от ученика (не тьютора) не должен долететь до тьютора.
        # За ним шлём валидный hint_revealed — тьютор получает ровно его.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            student_ws.send_json({"type": "attempts_changed", "task_id": 1, "status": None})  # отфильтровано
            student_ws.send_json({"type": "hint_revealed", "task_id": 81, "level": 1})  # валидное
            msg = tutor_ws.receive_json()
            assert msg["type"] == "hint_revealed"

    def test_hint_revealed_from_tutor_is_dropped(self, app, student_client, tutor_client, student):
        # hint_revealed от тьютора (должен идти от ученика) не доходит до
        # студента. За ним шлём валидный tutor_hint — студент получает его.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "hint_revealed", "task_id": 81, "level": 1})  # отфильтровано
            tutor_ws.send_json({"type": "tutor_hint", "code": "ok"})  # валидное
            msg = student_ws.receive_json()
            assert msg == {"type": "tutor_hint", "code": "ok"}


# --- Ссылка дозвона: доставка офлайн-ученику (feat.9) -------------------------

class TestCallLinkPending:
    """feat.9: тьютор отправил ссылку на созвон, пока ученик офлайн.

    Раньше ``call_link`` ретранслировался только в открытый сокет ученика и
    молча терялся. Теперь ссылка живёт в комнате (``pending_call_link``) и
    доносится рестейтом при каждом подключении ученика — пока тьютор не отменит
    её (``call_link_cancel``) или ученик не примет (``call_link_accepted``:
    сервер сам чистит pending и сообщает тьюторам — отзыв не зависит от того,
    жива ли ещё вкладка тьютора)."""

    URL = "https://telemost.yandex.ru/join/abc123"

    def test_link_sent_to_offline_student_delivered_on_connect(self, app, student_client, tutor_client, student):
        # Главный кейс feat.9: тьютор шлёт ссылку в пустую комнату → ученик
        # подключается → получает call_link третьим сообщением при подключении
        # (после tutor_status и tutor_hint).
        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as tutor_ws:
            _drain(tutor_ws, 3)
            tutor_ws.send_json({"type": "call_link", "url": self.URL})
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws:
                _drain(student_ws, 2)  # tutor_status, tutor_hint
                msg = student_ws.receive_json()
                assert msg == {"type": "call_link", "url": self.URL}

    def test_pending_link_survives_student_reconnect(self, app, student_client, tutor_client, student):
        # Ссылка живёт до отмены/принятия, а не до первой доставки: ученик,
        # переподключившийся (F5), снова получает её рестейтом.
        # NB: дисконнектные сообщения (call_end и student_status(online=False)
        # тьютору из finally ws.py) здесь НЕ проверяем и не дрейним: TestClient
        # на выходе из with гонится с отменой задачи приложения (starlette
        # 0.49: close → сразу cs.cancel), и эти две отправки недетерминированы
        # в тестах — можно зависнуть на receive. Само состояние комнаты к
        # моменту выхода чисто: __exit__ ждёт отработки finally. Проверяем
        # только сообщения обработчика ПОДКЛЮЧЕНИЯ — они детерминированы.
        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as tutor_ws:
            _drain(tutor_ws, 3)
            tutor_ws.send_json({"type": "call_link", "url": self.URL})
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws:
                _drain(student_ws, 3)  # tutor_status, tutor_hint, call_link
            # ученик ушёл и зашёл снова (F5) — ссылка всё ещё в комнате
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws2:
                _drain(student_ws2, 2)  # tutor_status, tutor_hint
                msg = student_ws2.receive_json()
                assert msg == {"type": "call_link", "url": self.URL}

    def test_cancel_before_connect_clears_pending(self, app, student_client, tutor_client, student):
        # Тьютор передумал до прихода ученика: call_link_cancel чистит pending,
        # при подключении ученик НЕ получает ссылку. Маркер после подключения
        # доказывает, что в очереди ничего не стояло (иначе он пришёл бы вторым).
        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as tutor_ws:
            _drain(tutor_ws, 3)
            tutor_ws.send_json({"type": "call_link", "url": self.URL})
            tutor_ws.send_json({"type": "call_link_cancel"})
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws:
                _drain(student_ws, 2)  # только tutor_status, tutor_hint
                tutor_ws.send_json({"type": "tutor_hint", "code": "маркер"})
                msg = student_ws.receive_json()
                assert msg == {"type": "tutor_hint", "code": "маркер"}

    def test_link_relayed_live_when_student_online(self, app, student_client, tutor_client, student):
        # Онлайн-ученик получает ссылку сразу, как и раньше (live-реле).
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "call_link", "url": self.URL})
            msg = student_ws.receive_json()
            assert msg == {"type": "call_link", "url": self.URL}

    def test_accepted_notifies_tutor_and_retracts_pending(self, app, student_client, tutor_client, student):
        # Ученик кликнул по трубке: тьютор получает call_link_accepted
        # («Принято»), а сервер сразу чистит pending — переподключившийся
        # ученик ссылки больше не получает (маркер приходит первым).
        # Дисконнектные сообщения тьютора не дрейним — см. NB в
        # test_pending_link_survives_student_reconnect.
        with tutor_client.websocket_connect(f"/ws/session/{student.id}") as tutor_ws:
            _drain(tutor_ws, 3)
            tutor_ws.send_json({"type": "call_link", "url": self.URL})
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws:
                _drain(student_ws, 3)  # tutor_status, tutor_hint, call_link
                _drain(tutor_ws, 1)    # student_status(online=True)
                student_ws.send_json({"type": "call_link_accepted"})
                msg = tutor_ws.receive_json()
                assert msg == {"type": "call_link_accepted"}
            with student_client.websocket_connect(f"/ws/session/{student.id}") as student_ws2:
                _drain(student_ws2, 2)  # tutor_status, tutor_hint — ссылки нет
                tutor_ws.send_json({"type": "tutor_hint", "code": "маркер"})
                msg = student_ws2.receive_json()
                assert msg == {"type": "tutor_hint", "code": "маркер"}

    def test_call_link_from_student_is_dropped(self, app, student_client, tutor_client, student):
        # call_link — только от тьютора: от ученика он не доходит до тьютора.
        # За ним валидный hint_revealed — тьютор получает ровно его.
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            student_ws.send_json({"type": "call_link", "url": self.URL})  # отфильтровано
            student_ws.send_json({"type": "hint_revealed", "task_id": 1, "level": 1})
            msg = tutor_ws.receive_json()
            assert msg["type"] == "hint_revealed"

    def test_call_link_accepted_from_tutor_is_dropped(self, app, student_client, tutor_client, student):
        # call_link_accepted — только от ученика: от тьютора он не доходит до
        # ученика (валидный tutor_hint-маркер приходит первым).
        with live_room(student_client, tutor_client, student.id) as (student_ws, tutor_ws):
            tutor_ws.send_json({"type": "call_link_accepted"})  # отфильтровано
            tutor_ws.send_json({"type": "tutor_hint", "code": "ok"})  # валидное
            msg = student_ws.receive_json()
            assert msg == {"type": "tutor_hint", "code": "ok"}
