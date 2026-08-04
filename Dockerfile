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
# Учебные ноутбуки (справочные материалы) лежат внутри webapp/content/notebooks/
# и едут в образ вместе с COPY webapp/ выше; отдельного конвертированного
# формата нет — materials.py читает .ipynb напрямую.

USER app
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
