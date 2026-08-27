# -*- coding: utf-8 -*-
"""API заданий и student-facing данных: список заданий, материалы, попытки
ученика, TURN-креды, отправка и свободный запуск кода."""
import base64
import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from webapp.config import STUN_URLS, TURN_SECRET, TURN_URLS
from webapp.core.auth import current_user_id, unauthorized
from webapp.core.db import get_db
from webapp.core.models import Attempt
from webapp.content.materials import MATERIALS_MANIFEST, get_lesson
from webapp.grading.bot_bridge import TASKS
from webapp.grading.grading import grade, run_free, run_with_sample
from webapp.grading.test_cases import TEST_CASES
from webapp.routes._common import SubmissionRequest, effective_identity, task_attempts, task_status_map

router = APIRouter()


@router.get("/api/tasks")
def list_tasks(request: Request):
    """Каталог заданий: id, условие, пример (только задания с тест-кейсами)."""
    if current_user_id(request) is None:
        return unauthorized()
    return [
        {"id": task_id, "description": TASKS[task_id]["description"], "example": TASKS[task_id]["example"]}
        for task_id in sorted(TEST_CASES)
    ]


@router.get("/api/materials")
def list_materials(request: Request):
    """Манифест материалов: модули → уроки (без содержимого уроков)."""
    if current_user_id(request) is None:
        return unauthorized()
    return MATERIALS_MANIFEST


@router.get("/api/materials/{module}/{lesson}")
def get_material(module: str, lesson: str, request: Request):
    """Один урок материалов: code-ячейки ноутбука с выводами (из памяти,
    см. content/materials.py)."""
    if current_user_id(request) is None:
        return unauthorized()
    data = get_lesson(module, lesson)
    if data is None:
        return JSONResponse(status_code=404, content={"error": "Материал не найден"})
    return data


@router.get("/api/turn-credentials")
def turn_credentials(request: Request):
    """ICE-серверы для WebRTC-звонка: STUN всегда; TURN — временная учётка
    (см. схему в коде ниже), статического пароля во фронте нет."""
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
    """Статус своих заданий ('pass'/'fail'); при имперсонации — задания
    ученика (effective_identity)."""
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return task_status_map(db, user_id)


@router.get("/api/attempts/mine/{task_id}")
def my_task_attempts(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Свои попытки по одному заданию; при имперсонации — ученика."""
    if current_user_id(request) is None:
        return unauthorized()
    user_id, _, _, _ = effective_identity(request, db)
    return task_attempts(db, user_id, task_id)


class SolveRunFreeRequest(BaseModel):
    """Код + опциональный task_id: с задачей «Запустить» гоняет код через
    харнесс с первым входом (run_with_sample), без задачи — как plain-скрипт
    (run_free, прежнее поведение)."""
    code: str
    task_id: int | None = None


@router.post("/api/solve/run_free")
def run_solve_code_free(payload: SolveRunFreeRequest, request: Request):
    """Свободный запуск кода ученика в его собственном редакторе. Для кода
    конкретного задания — с данными на входе (solve() вызывается харнессом),
    для свободного print-кода — без входа, как раньше."""
    if current_user_id(request) is None:
        return unauthorized()
    if payload.task_id is None:
        return run_free(payload.code)
    return run_with_sample(payload.task_id, payload.code)


@router.post("/api/submit")
def submit(payload: SubmissionRequest, request: Request, db: Session = Depends(get_db)):
    """Отправка решения на проверку (центральный эндпоинт грейдера): grade()
    прогоняет код на всех тестах; Attempt записывается только при реальном
    вердикте (не системной ошибке). В режиме имперсонации запрещено — тьютор
    не должен решать за ученика."""
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
