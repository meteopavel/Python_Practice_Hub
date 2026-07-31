# -*- coding: utf-8 -*-
"""Мост к банку заданий и эталонных решений в bot/ — общий источник
для Telegram-бота и веб-грейдера, чтобы не дублировать содержимое."""
import json
import sys
from pathlib import Path

_BOT_DIR = Path(__file__).resolve().parent.parent.parent / "bot"
if str(_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(_BOT_DIR))

# Не переиспользуем load_tasks_from_json.py напрямую: там путь к tasks.json
# относительный (рассчитан на запуск бота с cwd=bot/), а веб-приложение
# запускается из корня репозитория.
with open(_BOT_DIR / "tasks.json", "r", encoding="utf-8") as _f:
    _data = json.load(_f)
TASKS = {int(k): v for k, v in _data["tasks"].items()}

from solvers import get_solver  # noqa: E402
