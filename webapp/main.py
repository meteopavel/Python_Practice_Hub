# -*- coding: utf-8 -*-
"""FastAPI-приложение веб-грейдера. Оболочка: отдаёт список заданий,
логин/сессию и принимает решение ученика. Вся логика проверки —
в grading.py/sandbox.py, вся модель данных — в models.py."""
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from auth import authenticate, current_user_id
from bot_bridge import TASKS
from db import Base, SessionLocal, engine, get_db
from grading import grade
from models import Attempt
from test_cases import TEST_CASES

SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET не задан — см. env.example")

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
    return RedirectResponse(url="/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
def index(request: Request):
    if current_user_id(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tasks")
def list_tasks(request: Request):
    if current_user_id(request) is None:
        return JSONResponse(status_code=401, content={"error": "Не авторизован"})
    return [
        {"id": task_id, "description": TASKS[task_id]["description"], "example": TASKS[task_id]["example"]}
        for task_id in sorted(TEST_CASES)
    ]


@app.get("/api/me")
def me(request: Request):
    user_id = current_user_id(request)
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Не авторизован"})
    return {"username": request.session.get("username")}


@app.post("/api/submit")
def submit(payload: SubmissionRequest, request: Request, db: Session = Depends(get_db)):
    user_id = current_user_id(request)
    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Не авторизован"})

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
