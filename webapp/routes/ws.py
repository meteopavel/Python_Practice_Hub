# -*- coding: utf-8 -*-
"""WebSocket живой сессии тьютор↔ученик: мультиплексирует live-код, подсказки,
результаты проверок и сигналинг звонка/ссылки на созвон."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from webapp.core.models import ROLE_STUDENT, ROLE_TUTOR
from webapp.core.realtime import get_room, safe_send

router = APIRouter()


@router.websocket("/ws/session/{student_id}")
async def session_ws(websocket: WebSocket, student_id: int):
    """Живая комната одного ученика: сам ученик + один или несколько тьюторов,
    которые сейчас смотрят его экран. Тьютор пишет — ученик видит подсказку,
    ученик печатает — тьютор видит код в реальном времени."""
    user_id = websocket.session.get("user_id")
    role = websocket.session.get("role")
    if user_id is None or role not in (ROLE_STUDENT, ROLE_TUTOR):
        await websocket.close(code=4401)
        return
    if role == ROLE_STUDENT and user_id != student_id:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    room = get_room(student_id)
    is_tutor = role == ROLE_TUTOR

    if is_tutor:
        room.tutor_sockets.add(websocket)
        await safe_send(websocket, {
            "type": "student_code",
            "code": room.last_student_code,
            "task_id": room.last_student_task_id,
        })
        await safe_send(websocket, {"type": "tutor_hint", "code": room.last_tutor_hint})
        await safe_send(websocket, {"type": "student_status", "online": room.student_ws is not None})
        if room.student_ws is not None:
            await safe_send(room.student_ws, {"type": "tutor_status", "online": True})
    else:
        room.student_ws = websocket
        await safe_send(websocket, {"type": "tutor_status", "online": bool(room.tutor_sockets)})
        await safe_send(websocket, {"type": "tutor_hint", "code": room.last_tutor_hint})
        for tutor_ws in room.tutor_sockets:
            await safe_send(tutor_ws, {"type": "student_status", "online": True})

    try:
        while True:
            data = await websocket.receive_json()

            # Сигналинг звонка (SDP offer/answer, ICE-кандидаты, завершение) —
            # тот же канал, просто пересылаем сообщение как есть другой стороне
            # комнаты. Медиа (звук) идёт напрямую между браузерами по WebRTC,
            # сервер только сводит вдвоём и дальше не участвует.
            # call_link (2026-07-22) — замена самого WebRTC-звонка (см.
            # DEPRECATED-пометку в index.html/tutor_student.html): тьютор
            # созванивается с учеником во внешнем сервисе (Телемост и т.п.)
            # и просто присылает ссылку тем же каналом, сервер её ретранслирует
            # как есть, никакой обработки/хранения. call_link_ack — ученик
            # подтверждает тьютору, что ссылка реально дошла и отрендерилась.
            if data.get("type") in (
                "call_offer", "call_answer", "call_ice", "call_end", "mute_status",
                "call_link", "call_link_ack", "call_link_cancel",
            ):
                if is_tutor:
                    if room.student_ws is not None:
                        await safe_send(room.student_ws, data)
                else:
                    for tutor_ws in room.tutor_sockets:
                        await safe_send(tutor_ws, data)
                continue

            # Результат прогона кода в редакторе подсказки — только тьютор
            # запускает, ученику просто пересылаем результат посмотреть.
            # hint_visibility — тьютор открывает/закрывает подсказку "замком".
            if data.get("type") in ("hint_result", "hint_free_result", "hint_visibility"):
                if is_tutor and room.student_ws is not None:
                    await safe_send(room.student_ws, data)
                continue

            # Результат отправки решения учеником (кнопка "Проверить" в своём
            # редакторе) — тьютор должен увидеть его сразу, а не только когда
            # сам откроет "Попытки ученика".
            # hint_revealed — ученик раскрыл ступень подсказки (bug.3): тьютору
            # надо тут же перерисовать панель подсказок без F5, как и попытки.
            # Оба события однонаправленные student→tutor, поэтому идут вместе.
            if data.get("type") in ("submit_result", "hint_revealed"):
                if not is_tutor:
                    for tutor_ws in room.tutor_sockets:
                        await safe_send(tutor_ws, data)
                continue

            # Тьютор правит код ученика напрямую (по кнопке) — применяется
            # у ученика как обычный live-код, поэтому и статус, и мираж у
            # тьютора обновятся тем же путём, что при обычном наборе текста.
            if data.get("type") == "tutor_edit_code":
                if is_tutor and room.student_ws is not None:
                    await safe_send(room.student_ws, data)
                continue

            # Тьютор откатил задание как выполненное (feat.2): ученик должен
            # сразу увидеть обнуление — точка/индикатор «решено» пропадает
            # live, без F5. Симметрично submit_result в обратную сторону.
            if data.get("type") == "solved_reverted":
                if is_tutor and room.student_ws is not None:
                    await safe_send(room.student_ws, data)
                continue

            code = data.get("code", "")
            task_id = data.get("task_id")
            if is_tutor:
                room.last_tutor_hint = code
                if room.student_ws is not None:
                    await safe_send(room.student_ws, {"type": "tutor_hint", "code": code})
            else:
                room.last_student_code = code
                room.last_student_task_id = task_id
                for tutor_ws in room.tutor_sockets:
                    await safe_send(tutor_ws, {"type": "student_code", "code": code, "task_id": task_id})
    except WebSocketDisconnect:
        pass
    finally:
        if is_tutor:
            room.tutor_sockets.discard(websocket)
            if room.student_ws is not None:
                # Обрыв связи с тьютором посреди звонка должен сразу сбросить
                # состояние у ученика, а не ждать ICE-таймаут.
                await safe_send(room.student_ws, {"type": "call_end"})
                if not room.tutor_sockets:
                    await safe_send(room.student_ws, {"type": "tutor_status", "online": False})
        elif room.student_ws is websocket:
            room.student_ws = None
            for tutor_ws in room.tutor_sockets:
                await safe_send(tutor_ws, {"type": "call_end"})
                await safe_send(tutor_ws, {"type": "student_status", "online": False})
