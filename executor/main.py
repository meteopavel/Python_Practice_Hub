# -*- coding: utf-8 -*-
"""Исполнитель — работает только внутри тоннеля (10.0.0.1 на роутере),
наружу не смотрит. Единственная задача: безопасно прогнать код ученика
и вернуть результат. Ничего не знает про задания/эталоны — это забота
фронта (webapp/), который живёт на Frankfurt."""
from fastapi import FastAPI
from pydantic import BaseModel

from sandbox import run_free_code, run_student_code

app = FastAPI(title="Python Practice Hub — исполнитель")


class RunRequest(BaseModel):
    code: str
    test_input: object


class RunFreeRequest(BaseModel):
    code: str


@app.post("/run")
def run(payload: RunRequest):
    return run_student_code(payload.code, payload.test_input)


@app.post("/run_free")
def run_free(payload: RunFreeRequest):
    return run_free_code(payload.code)


@app.get("/health")
def health():
    return {"ok": True}
