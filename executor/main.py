# -*- coding: utf-8 -*-
"""Исполнитель — работает только внутри тоннеля на роутере,
наружу не смотрит. Единственная задача: безопасно прогнать код ученика
и вернуть результат. Ничего не знает про задания/эталоны — это забота
фронта (webapp/), который живёт на VPS."""
from fastapi import FastAPI
from pydantic import BaseModel

from sandbox import run_free_code, run_student_code

app = FastAPI(title="Python Practice Hub — исполнитель")


class RunRequest(BaseModel):
    """Прогон задания: код ученика (обязан определить solve) + тестовый вход."""

    code: str
    test_input: object


class RunFreeRequest(BaseModel):
    """Свободный прогон: только код, без входа и харнесса."""

    code: str


@app.post("/run")
def run(payload: RunRequest):
    """Прогон кода с входом через харнесс (sandbox.run_student_code)."""
    return run_student_code(payload.code, payload.test_input)


@app.post("/run_free")
def run_free(payload: RunFreeRequest):
    """Свободный прогон без харнесса (sandbox.run_free_code)."""
    return run_free_code(payload.code)


@app.get("/health")
def health():
    """Живость исполнителя — для деплоя и мониторинга."""
    return {"ok": True}
