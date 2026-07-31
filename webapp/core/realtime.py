# -*- coding: utf-8 -*-
"""In-memory realtime-комнаты для живых сессий тьютор-ученик.

Комната = один ученик. Состояние живёт, пока жив процесс приложения — рестарт
контейнера просто обнуляет текущие live-сессии, и это ожидаемо: это сиюминутное
состояние (кто сейчас печатает), а не история попыток (та в БД)."""
from fastapi import WebSocket


class Room:
    def __init__(self):
        self.student_ws: WebSocket | None = None
        self.tutor_sockets: set[WebSocket] = set()
        self.last_student_code = ""
        self.last_student_task_id: int | None = None
        self.last_tutor_hint = ""


rooms: dict[int, Room] = {}


def get_room(student_id: int) -> Room:
    if student_id not in rooms:
        rooms[student_id] = Room()
    return rooms[student_id]


async def safe_send(websocket: WebSocket, payload: dict) -> None:
    """Отправка соседу по комнате не должна ронять цикл отправителя, если
    сосед уже отвалился, а disconnect ещё не долетел до finally."""
    try:
        await websocket.send_json(payload)
    except Exception:
        pass
