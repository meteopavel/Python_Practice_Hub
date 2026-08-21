# -*- coding: utf-8 -*-
"""FastAPI-приложение веб-грейдера. Создаёт app, монтирует статику, сессию и
роутеры. Вся логика проверки — в grading/, модель данных — в core/models.py,
роуты — в routes/."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from webapp.config import SESSION_SECRET, STATIC_DIR
from webapp.core.db import Base, engine
from webapp.routes import auth, hints_api, pages, students, tasks_api, tutor_api, ws

app = FastAPI(title="Доброкод — веб-грейдер")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


for _router in (auth.router, pages.router, tasks_api.router, students.router,
                hints_api.router, tutor_api.router, ws.router):
    app.include_router(_router)
