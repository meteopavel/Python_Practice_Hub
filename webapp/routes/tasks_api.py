# -*- coding: utf-8 -*-
"""API заданий и student-facing данных: список заданий, материалы, попытки
ученика, TURN-креды, отправка и свободный запуск кода."""
import base64
import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from webapp.config import STUN_URLS, TURN_SECRET, TURN_URLS
from webapp.core.auth import current_user_id, unauthorized
from webapp.core.db import get_db
from webapp.core.models import Attempt
from webapp.content.materials import MATERIALS_MANIFEST, get_lesson
from webapp.grading.bot_bridge import TASKS
from webapp.grading.grading import grade, run_free
from webapp.grading.test_cases import TEST_CASES
from webapp.routes._common import HintFreeRunRequest, SubmissionRequest, effective_identity, task_attempts, task_status_map

router = APIRouter()


@router.get("/api/tasks")
def list_tasks(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    return [
        {"id": task_id, "description": TASKS[task_id]["description"], "example": TASKS[task_id]["example"]}
        for task_id in sorted(TEST_CASES)
    ]


@router.get("/api/materials")
def list_materials(request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    return MATERIALS_MANIFEST


@router.get("/api/materials/{module}/{lesson}")
def get_material(module: str, lesson: str, request: Request):
    if current_user_id(request) is None:
        return unauthorized()
    data = get_lesson(module, lesson)
    if data is None:
        return JSONResponse(status_code=404, content={"error": "Материал не найден"})
    return data


@router.get("/api/turn-credentials")
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


@router.get("/api/attempts/mine")
def my_attempts(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return task_status_map(db, user_id)


@router.get("/api/attempts/mine/{task_id}")
def my_task_attempts(task_id: int, request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return task_attempts(db, user_id, task_id)


@router.post("/api/solve/run_free")
def run_solve_code_free(payload: HintFreeRunRequest, request: Request):
    """Свободный запуск кода ученика в его собственном редакторе — без сверки
    с эталоном, чтобы можно было просто написать print(...) и посмотреть вывод."""
    if current_user_id(request) is None:
        return unauthorized()
    return run_free(payload.code)


@router.post("/api/submit")
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
