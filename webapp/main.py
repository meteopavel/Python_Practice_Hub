# -*- coding: utf-8 -*-
"""FastAPI-приложение веб-грейдера. Оболочка: отдаёт список заданий,
логин/сессию и принимает решение ученика. Вся логика проверки —
в grading.py/sandbox.py, вся модель данных — в models.py."""
import base64
import hashlib
import hmac
import inspect
import os
import time
from pathlib import Path

import httpx

from fastapi import Depends, FastAPI, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from auth import authenticate, current_user_id, current_user_role, forbidden, hash_password, unauthorized
from bot_bridge import TASKS, get_solver
from db import Base, SessionLocal, engine, get_db
from grading import grade, run_free
from hints import HINTED_TASK_IDS, LEVELS, available_levels, can_reveal, has_hints, record_reveal, render_markdown, reset_reveal_cascade
from materials import MATERIALS_MANIFEST, get_lesson
from models import ROLE_STUDENT, ROLE_TUTOR, Attempt, Hint, HintReveal, User
from realtime import get_room, safe_send
from test_cases import TEST_CASES

SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET не задан — см. env.example")

# TURN — на случай, если STUN не пробивает NAT (симметричный NAT, часть
# провайдеров/файрволов). Без TURN_SECRET/TURN_URLS отдаём только STUN —
# работает для локальной разработки, не работает во всех сетях в проде.
TURN_SECRET = os.environ.get("TURN_SECRET")
TURN_URLS = os.environ.get("TURN_URLS")
STUN_URLS = os.environ.get("STUN_URLS", "stun:informatika.meteopavel.space:3478")

# tutor-llm — отдельный микросервис на роутере (как executor, см.
# tutor-llm/). Проксирует запросы тьютора в DeepSeek API. Ключ DeepSeek
# живёт только в контейнере tutor-llm, сюда не пробрасывается.
TUTOR_LLM_URL = os.environ.get("TUTOR_LLM_URL", "http://10.0.0.1:8011")

app = FastAPI(title="Python Practice Hub — веб-грейдер")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


class SubmissionRequest(BaseModel):
    task_id: int
    code: str


class HintFreeRunRequest(BaseModel):
    code: str


class TutorAskRequest(BaseModel):
    """Запрос тьютора к ИИ-помощнику. task_context/student_code опциональны —
    можно спросить и без них. question обязателен."""
    task_context: str | None = None   # текст задания / условие
    student_code: str | None = None   # код ученика (если есть)
    question: str


class HintRevealRequest(BaseModel):
    """Ученик запрашивает раскрытие уровня подсказки. level — 1|2|3."""
    level: int


class HintResetRequest(BaseModel):
    """Тьютор сбрасывает раскрытый уровень подсказки ученика (level — 1|2|3).
    Сбрасывается сам уровень и все раскрытые уровни выше него по цепочке."""
    level: int


class HintContentRequest(BaseModel):
    """Тьютор сохраняет текст уровня (markdown)."""
    content: str = ""


@app.get("/login")
def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@app.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate(db, username, password)
    if user is None:
        return RedirectResponse(url="/login?error=1", status_code=303)
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    return RedirectResponse(url="/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    # Тьютор без имперсонации попадает на список учеников — это теперь его
    # главная страница, отдельного /tutor больше нет. Во время имперсонации
    # (эффективная роль student) видит ровно ту же index.html, что и ученик.
    _, impersonating, _, _ = effective_identity(request, db)
    if current_user_role(request) == ROLE_TUTOR and not impersonating:
        return FileResponse(STATIC_DIR / "tutor.html")
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/tutor")
def tutor_page(request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.get("/tutor/student/{student_id}")
def tutor_student_page(student_id: int, request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(STATIC_DIR / "tutor_student.html")


@app.get("/tutor/hints")
def tutor_hints_page(request: Request):
    """Админка подсказок для заданий 81..100 — тьютор правит тексты уровней."""
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(STATIC_DIR / "tutor_hints.html")


@app.post("/tutor/student/{student_id}/impersonate")
def start_impersonation(student_id: int, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    student = db.query(User).filter(User.id == student_id, User.role == ROLE_STUDENT).first()
    if student is not None:
        # Эффективная личность только для student-facing данных (см.
        # effective_identity) — авторизация тьюторских роутов идёт по
        # реальной роли из сессии и этим флагом не затрагивается.
        request.session["impersonate_student_id"] = student.id
    return RedirectResponse(url="/", status_code=303)


@app.post("/impersonate/stop")
def stop_impersonation(request: Request):
    student_id = request.session.pop("impersonate_student_id", None)
    if student_id is not None:
        return RedirectResponse(url=f"/tutor/student/{student_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.get("/materials/{module}/{lesson}")
def materials_page(module: str, lesson: str, request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if get_lesson(module, lesson) is None:
        return JSONResponse(status_code=404, content={"error": "Материал не найден"})
    return FileResponse(STATIC_DIR / "materials.html")


def effective_identity(request: Request, db: Session):
    """Для тьютора в режиме "посмотреть как ученик" подменяет личность только
    для student-facing данных (список заданий/свои попытки) — НЕ для
    авторизации, та остаётся на реальной роли из сессии."""
    real_role = current_user_role(request)
    impersonate_id = request.session.get("impersonate_student_id")
    if impersonate_id and real_role == ROLE_TUTOR:
        student = db.query(User).filter(User.id == impersonate_id, User.role == ROLE_STUDENT).first()
        if student is not None:
            return student.id, True, request.session.get("username"), student.username
    return current_user_id(request), False, None, request.session.get("username")


@app.get("/api/tasks")
def list_tasks(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    return [
        {"id": task_id, "description": TASKS[task_id]["description"], "example": TASKS[task_id]["example"]}
        for task_id in sorted(TEST_CASES)
    ]


@app.get("/api/materials")
def list_materials(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    return MATERIALS_MANIFEST


@app.get("/api/materials/{module}/{lesson}")
def get_material(module: str, lesson: str, request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    data = get_lesson(module, lesson)
    if data is None:
        return JSONResponse(status_code=404, content={"error": "Материал не найден"})
    return data


@app.get("/api/solution/{task_id}")
def get_solution(task_id: int, request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    oracle = get_solver(task_id)
    if oracle is None:
        return JSONResponse(status_code=404, content={"error": f"Эталон для задания {task_id} не найден"})
    return {"task_id": task_id, "source": inspect.getsource(oracle)}


@app.get("/api/turn-credentials")
def turn_credentials(request: Request):
    if current_user_id(request) is None:
        return unauthorized()

    ice_servers = [{"urls": STUN_URLS.split(",")}]
    if TURN_SECRET and TURN_URLS:
        # Временные учётки по схеме TURN REST API (coturn use-auth-secret):
        # username = "<unix-timestamp-истечения>:<метка>", credential — HMAC-SHA1
        # от username на общем секрете. Никакого статичного пароля во фронте.
        username = f"{int(time.time()) + 3600}:{request.session.get('username', 'user')}"
        digest = hmac.new(TURN_SECRET.encode(), username.encode(), hashlib.sha1).digest()
        credential = base64.b64encode(digest).decode()
        ice_servers.append({
            "urls": TURN_URLS.split(","),
            "username": username,
            "credential": credential,
        })
    return {"iceServers": ice_servers}


@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    user_id, impersonating, real_username, username = effective_identity(request, db)
    return {
        "id": user_id,
        "username": username,
        "role": ROLE_STUDENT if impersonating else request.session.get("role"),
        "impersonating": impersonating,
        "real_username": real_username,
    }


def _task_status_map(db: Session, user_id: int) -> dict:
    """task_id -> 'pass'/'fail' по всей истории попыток пользователя — 'pass'
    если хоть одна попытка когда-либо прошла. Общий код для своей истории
    (эффективная личность) и истории конкретного ученика (вид тьютора)."""
    rows = db.query(Attempt.task_id, Attempt.passed).filter(Attempt.user_id == user_id).all()
    passed_by_task = {}
    for task_id, passed in rows:
        passed_by_task[task_id] = passed_by_task.get(task_id, False) or passed
    return {task_id: ("pass" if passed else "fail") for task_id, passed in passed_by_task.items()}


def _task_attempts(db: Session, user_id: int, task_id: int) -> list:
    rows = (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id, Attempt.task_id == task_id)
        .order_by(Attempt.created_at.asc())
        .all()
    )
    return [
        {
            "passed": a.passed,
            "code": a.code,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


@app.get("/api/attempts/mine")
def my_attempts(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return _task_status_map(db, user_id)


@app.get("/api/attempts/mine/{task_id}")
def my_task_attempts(task_id: int, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return _task_attempts(db, user_id, task_id)


@app.get("/api/students")
def list_students(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    students = db.query(User).filter(User.role == ROLE_STUDENT).order_by(User.username).all()
    result = []
    for student in students:
        last_attempt = (
            db.query(Attempt)
            .filter(Attempt.user_id == student.id)
            .order_by(Attempt.created_at.desc())
            .first()
        )
        attempts_count = db.query(Attempt).filter(Attempt.user_id == student.id).count()
        result.append({
            "id": student.id,
            "username": student.username,
            "attempts_count": attempts_count,
            "last_attempt_at": last_attempt.created_at.isoformat() if last_attempt and last_attempt.created_at else None,
        })
    return result


class CreateStudentRequest(BaseModel):
    username: str
    password: str


@app.post("/api/students")
def create_student(payload: CreateStudentRequest, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    username = payload.username.strip()
    if not username or not payload.password:
        return JSONResponse(status_code=400, content={"error": "Логин и пароль не должны быть пустыми"})
    if db.query(User).filter(User.username == username).first() is not None:
        return JSONResponse(status_code=400, content={"error": f"Логин «{username}» уже занят"})
    student = User(username=username, password_hash=hash_password(payload.password), role=ROLE_STUDENT)
    db.add(student)
    db.commit()
    return {"id": student.id, "username": student.username}


class SetPasswordRequest(BaseModel):
    password: str


@app.post("/api/students/{student_id}/password")
def set_student_password(student_id: int, payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if not payload.password:
        return JSONResponse(status_code=400, content={"error": "Пароль не должен быть пустым"})
    student = db.query(User).filter(User.id == student_id, User.role == ROLE_STUDENT).first()
    if student is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    student.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


def _require_student(db: Session, student_id: int):
    return db.query(User).filter(User.id == student_id, User.role == ROLE_STUDENT).first()


@app.get("/api/students/{student_id}/attempts/status")
def student_task_status(student_id: int, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if _require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    return _task_status_map(db, student_id)


@app.get("/api/students/{student_id}/attempts/{task_id}")
def student_task_attempts(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if _require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    return _task_attempts(db, student_id, task_id)


@app.get("/api/students/{student_id}/hints/{task_id}")
def student_hints(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    """Состояние подсказок задания для конкретного ученика — глазами тьютора
    (мониторинг прогресса раскрытия, без reveal-кнопок). Та же логика, что у
    ученического GET /api/hints, но user_id берётся явно из student_id, а не
    из effective_identity. Контент отдаётся для revealed (тьютор видит, что
    именно ученик уже прочитал)."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if _require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    return _hints_response(db, student_id, task_id)


@app.post("/api/students/{student_id}/hints/{task_id}/reset")
def reset_student_hint(student_id: int, task_id: int, payload: HintResetRequest, request: Request, db: Session = Depends(get_db)):
    """Тьютор сбрасывает раскрытый уровень подсказки ученика — ученик снова
    увидит его закрытым (как будто не открывал). Сбрасывается сам уровень и
    каскадно все раскрытые уровни выше, чтобы не получить невозможное
    состояние «старший открыт, а его якорь закрыт». Действие необратимо:
    истории раскрытия в БД нет. Возвращает свежее состояние подсказок."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if _require_student(db, student_id) is None:
        return JSONResponse(status_code=404, content={"error": "Ученик не найден"})
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if payload.level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Неверный уровень подсказки"})
    reset_reveal_cascade(db, student_id, task_id, payload.level)
    return _hints_response(db, student_id, task_id)


@app.websocket("/ws/session/{student_id}")
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
                "call_link", "call_link_ack",
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
            if data.get("type") == "submit_result":
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


@app.post("/api/solve/run_free")
def run_solve_code_free(payload: HintFreeRunRequest, request: Request):
    """Свободный запуск кода ученика в его собственном редакторе — без сверки
    с эталоном, чтобы можно было просто написать print(...) и посмотреть вывод."""
    if current_user_id(request) is None:
        return unauthorized()
    return run_free(payload.code)


@app.post("/api/submit")
def submit(payload: SubmissionRequest, request: Request, db: Session = Depends(get_db)):
    user_id = current_user_id(request)
    if user_id is None:
        return unauthorized()
    if request.session.get("impersonate_student_id"):
        return JSONResponse(status_code=403, content={"error": "Отправка кода недоступна в режиме просмотра «как ученик»"})

    result = grade(payload.task_id, payload.code)

    # Записываем попытку только если грейдер реально отработал (не системная
    # ошибка вроде недоступного исполнителя) — иначе это не попытка ученика.
    if "all_passed" in result:
        db.add(Attempt(
            user_id=user_id,
            task_id=payload.task_id,
            code=payload.code,
            passed=result["all_passed"],
        ))
        db.commit()

    return result


@app.post("/api/hint/run")
def run_hint_code(payload: SubmissionRequest, request: Request):
    """Тьютор проверяет код прямо в редакторе подсказки — тот же grade(),
    но без записи Attempt: это демонстрация ученику, а не его попытка."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    return grade(payload.task_id, payload.code)


@app.post("/api/hint/run_free")
def run_hint_code_free(payload: HintFreeRunRequest, request: Request):
    """Свободный запуск кода в подсказке — без сверки с эталоном, просто
    исполняет код как есть (print() и любые операторы отрабатывают)."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    return run_free(payload.code)


@app.post("/api/tutor/ask")
def tutor_ask(payload: TutorAskRequest, request: Request):
    """Тьютор спрашивает ИИ-помощника (DeepSeek через микросервис tutor-llm
    на роутере). Прокси: webapp не знает ключ DeepSeek, он только пересылает
    структурированный запрос в tutor-llm по внутренней сети (как executor).
    Только для роли tutor."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()

    try:
        response = httpx.post(
            f"{TUTOR_LLM_URL}/ask",
            json=payload.model_dump(),
            timeout=70.0,  # чуть больше, чем 60-секундный таймаут tutor-llm → DeepSeek
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        # tutor-llm ответил ошибкой (скорее всего 502 от DeepSeek или 500 — нет ключа)
        return JSONResponse(
            status_code=exc.response.status_code,
            content={"error": f"tutor-llm: {exc.response.text[:300]}"},
        )
    except httpx.HTTPError as exc:
        # tutor-llm недоступен (контейнер не поднят / тоннель упал)
        return JSONResponse(
            status_code=502,
            content={"error": f"tutor-llm недоступен ({TUTOR_LLM_URL}): {exc}"},
        )


# --- Многоступенчатые подсказки (задания 81..100) --------------------------
# Механика независима от live-сессии тьютора: это курированные подсказки,
# которые ученик открывает по таймеру, а не то, что тьютор пишет ему вживую.
# Логика тайминга и доступа — в hints.py, эндпоинты здесь только проверяют
# авторизацию и валидируют task_id/level.


def _hints_response(db: Session, user_id: int, task_id: int) -> dict:
    """Общий вид ответа с состоянием подсказок для ученика — используется и в
    GET, и в POST /reveal, чтобы контракт был единый. Контент рендерим в HTML
    только для revealed (ученик видит готовый текст, не сырой markdown)."""
    levels = available_levels(db, user_id, task_id)
    for item in levels:
        if item.get("status") == "revealed":
            item["content_html"] = render_markdown(item.get("content", ""))
            item.pop("content", None)
    return {"task_id": task_id, "levels": levels}


@app.get("/api/hints/{task_id}")
def get_hints(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Состояние подсказок задания для ученика: по уровню — статус (locked /
    waiting / ready / revealed), для revealed — отрендеренный HTML контента,
    для waiting — available_at (когда станет ready, сервер считает тайминг).

    Контент отдаётся только для уже раскрытых уровней; для waiting сервер
    остаётся источником правды о готовности — фронт по обнулении таймера
    перезапрашивает это состояние."""
    if current_user_id(request) is None:
        return unauthorized()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    user_id, _, _, _ = effective_identity(request, db)
    return _hints_response(db, user_id, task_id)


@app.post("/api/hints/{task_id}/reveal")
def reveal_hint(task_id: int, payload: HintRevealRequest, request: Request, db: Session = Depends(get_db)):
    """Ученик раскрывает уровень подсказки. Сервер решает, можно ли сейчас
    раскрыть (предыдущий уровень раскрыт И его задержка прошла), иначе 409.
    Повторный запрос на уже раскрытый уровень — идемпотентен (не создаёт
    дубль и не сдвигает revealed_at)."""
    if current_user_id(request) is None:
        return unauthorized()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if payload.level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Уровень должен быть 1, 2 или 3"})
    user_id, _, _, _ = effective_identity(request, db)
    if not can_reveal(db, user_id, task_id, payload.level):
        return JSONResponse(
            status_code=409,
            content={"error": "Уровень пока недоступен — подождите или раскройте предыдущую ступень"},
        )
    record_reveal(db, user_id, task_id, payload.level)
    return _hints_response(db, user_id, task_id)


# --- Админка подсказок (только тьютор) -------------------------------------


@app.get("/api/admin/hints")
def admin_list_hints(request: Request, task_id: int, db: Session = Depends(get_db)):
    """Текст всех трёх уровней задания (включая пустые) — для редактора
    тьютора. Отдаём сырой markdown, не HTML: в форме его правят как текст."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    rows = db.query(Hint).filter(Hint.task_id == task_id).all()
    by_level = {r.level: r.content for r in rows}
    return {"task_id": task_id, "levels": [{"level": lvl, "content": by_level.get(lvl, "")} for lvl in LEVELS]}


@app.put("/api/admin/hints/{task_id}/{level}")
def admin_save_hint(task_id: int, level: int, payload: HintContentRequest, request: Request, db: Session = Depends(get_db)):
    """Сохранить (upsert) текст уровня подсказки. Контент — markdown,
    правит тьютор. Создание/обновление одной записью на (task_id, level)."""
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    if not has_hints(task_id):
        return JSONResponse(status_code=404, content={"error": "Подсказки для этого задания не предусмотрены"})
    if level not in LEVELS:
        return JSONResponse(status_code=400, content={"error": "Уровень должен быть 1, 2 или 3"})
    row = db.query(Hint).filter(Hint.task_id == task_id, Hint.level == level).first()
    if row is None:
        db.add(Hint(task_id=task_id, level=level, content=payload.content))
    else:
        row.content = payload.content
    db.commit()
    return {"task_id": task_id, "level": level, "content": payload.content}


# Список заданий с подсказками — для селектора в админке (номер + описание,
# чтобы тьютору было понятно, какое задание он правит).
@app.get("/api/admin/hints/tasks")
def admin_hinted_tasks(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    if current_user_role(request) != ROLE_TUTOR:
        return forbidden()
    return [
        {"id": task_id, "description": TASKS[task_id]["description"]}
        for task_id in sorted(HINTED_TASK_IDS)
    ]
