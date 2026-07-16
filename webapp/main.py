# -*- coding: utf-8 -*-
"""FastAPI-приложение веб-грейдера. Оболочка: отдаёт список заданий и
принимает решение ученика. Вся логика проверки — в grading.py/sandbox.py."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bot_bridge import TASKS
from grading import grade
from test_cases import TEST_CASES

app = FastAPI(title="Python Practice Hub — веб-грейдер")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SubmissionRequest(BaseModel):
    task_id: int
    code: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tasks")
def list_tasks():
    return [
        {"id": task_id, "description": TASKS[task_id]["description"], "example": TASKS[task_id]["example"]}
        for task_id in sorted(TEST_CASES)
    ]


@app.post("/api/submit")
def submit(payload: SubmissionRequest):
    return grade(payload.task_id, payload.code)
