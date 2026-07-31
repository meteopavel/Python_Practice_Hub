# -*- coding: utf-8 -*-
"""Страничные роуты: отдача Jinja2-шаблонов (практика, тьютор, материалы)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from webapp.config import templates
from webapp.core.auth import current_user_id, current_user_role
from webapp.core.db import get_db
from webapp.core.models import ROLE_TUTOR
from webapp.content.materials import get_lesson
from webapp.routes._common import effective_identity

router = APIRouter()


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    # Тьютор без имперсонации попадает на список учеников — это теперь его
    # главная страница, отдельного /tutor больше нет. Во время имперсонации
    # (эффективная роль student) видит ровно ту же index.html, что и ученик.
    _, impersonating, _, _ = effective_identity(request, db)
    if current_user_role(request) == ROLE_TUTOR and not impersonating:
        return templates.TemplateResponse(request, "tutor.html")
    return templates.TemplateResponse(request, "index.html")


@router.get("/tutor")
def tutor_page(request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@router.get("/tutor/student/{student_id}")
def tutor_student_page(student_id: int, request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "tutor_student.html")


@router.get("/tutor/hints")
def tutor_hints_page(request: Request):
    """Админка подсказок для заданий 81..100 — тьютор правит тексты уровней."""
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if current_user_role(request) != ROLE_TUTOR:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "tutor_hints.html")


@router.get("/materials/{module}/{lesson}")
def materials_page(module: str, lesson: str, request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    if get_lesson(module, lesson) is None:
        return JSONResponse(status_code=404, content={"error": "Материал не найден"})
    return templates.TemplateResponse(request, "materials.html")
