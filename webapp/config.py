# -*- coding: utf-8 -*-
"""Чтение конфигурации из окружения. Импортируется main.py и роутами."""
import mimetypes
import os
from pathlib import Path

from fastapi.templating import Jinja2Templates

# Регистрация MIME-типов шрифтов: на некоторых Linux-образах (включая
# Docker) .woff2 не зарегистрирован в системной mimetypes-таблице, и
# Starlette StaticFiles отдаёт шрифт как application/octet-stream, из-за
# чего браузер его отклоняет. Регистрируем канонические font/* типы.
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")

# webapp/ лежит в репозитории; static/ и templates/ — её подпапки.
# Пути вычисляются от этого файла, чтобы работать из любого cwd (корень репо
# при локальном запуске, /app — в контейнере).
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# templates живёт здесь, а не в main.py, чтобы избежать циклического импорта:
# роуты импортируют templates, а main импортирует роуты.
templates = Jinja2Templates(directory=TEMPLATES_DIR)

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
TUTOR_LLM_URL = os.environ.get("TUTOR_LLM_URL")
if not TUTOR_LLM_URL:
    raise RuntimeError("TUTOR_LLM_URL не задан — см. env.example")
