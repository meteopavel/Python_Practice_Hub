# -*- coding: utf-8 -*-
"""FastAPI-приложение веб-грейдера. Создаёт app, монтирует статику, сессию и
роутеры. Вся логика проверки — в grading/, модель данных — в core/models.py,
роуты — в routes/."""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from webapp.config import SESSION_SECRET, STATIC_DIR
from webapp.core.db import Base, engine
from webapp.routes import auth, hints_api, pages, students, tasks_api, tutor_api, ws

app = FastAPI(title="Доброкод — веб-грейдер")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# StaticFiles отдаёт только ETag/Last-Modified, без явного Cache-Control браузер
# держит JS/CSS в эвристическом кеше — после деплоя правки видны только по
# Ctrl+Shift+R (bug.15). no-cache = «хранить, но перед использованием
# ревалидировать»: условный запрос с If-None-Match получает дешёвый 304 от
# StaticFiles, а изменившийся файл — свежий 200. HTML — та же логика, чтобы сам
# документ не зависал устаревшим. API/JSON не кешируются эвристически (без
# Last-Modified), им заголовок не нужен.
@app.middleware("http")
async def cache_policy(request: Request, call_next):
    """Cache-Control: no-cache для /static/ и HTML — браузер ревалидирует
    (дешёвый 304 по ETag), а не держит старые JS/CSS после деплоя (bug.15)."""
    response = await call_next(request)
    if request.url.path.startswith("/static/") or response.headers.get(
        "content-type", ""
    ).startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.on_event("startup")
def create_tables():
    """Создать отсутствующие таблицы на старте (create_all идемпотентен;
    системы миграций в проекте нет)."""
    Base.metadata.create_all(bind=engine)


for _router in (auth.router, pages.router, tasks_api.router, students.router,
                hints_api.router, tutor_api.router, ws.router):
    app.include_router(_router)
