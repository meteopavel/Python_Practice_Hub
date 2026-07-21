FROM python:3.11-slim

RUN useradd --create-home --shell /usr/sbin/nologin app
WORKDIR /app

COPY webapp/requirements.txt webapp/requirements.txt
RUN pip install --no-cache-dir -r webapp/requirements.txt

# Только то, что реально импортирует webapp/bot_bridge.py — не тащим в образ
# python-telegram-bot и остальной bot/, который вебке не нужен.
# --chmod нужен: исходники на хосте местами лежат с правами 700, non-root
# пользователю app иначе будет нечем их прочитать.
COPY --chmod=755 bot/solvers.py bot/tasks.json bot/
COPY --chmod=755 webapp/ webapp/

# Справочные материалы (учебные ноутбуки) — webapp/materials.py читает их
# напрямую, отдельного конвертированного формата нет.
COPY --chmod=755 1_introduction 1_introduction/
COPY --chmod=755 2_loops_and_conditions 2_loops_and_conditions/
COPY --chmod=755 3_functions 3_functions/
COPY --chmod=755 4_dicts_and_sets 4_dicts_and_sets/
COPY --chmod=755 5_strings 5_strings/

USER app
WORKDIR /app/webapp
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
