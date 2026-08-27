# -*- coding: utf-8 -*-
"""Дамп всех таблиц БД в виде SQL INSERT-ов (в stdout).

Схему не дампим: она живёт в webapp/core/models.py и пересоздаётся
Base.metadata.create_all при старте приложения. Восстановление — поднять
чистую БД, запустить приложение (создаст таблицы), затем залить дамп:
    mysql -u <логин> -p <база> < dobrokod-db.sql

Использование (на проде — из контейнера app на Frankfurt, БД доступна
только оттуда):
    docker compose exec -T app python -m webapp.scripts.dump_db > dobrokod-db.sql

SQL пишется в stdout, сводка «таблица → строк» — в stderr, чтобы вывод
можно было перенаправлять в файл не фильтруя. Таблицы идут в порядке
FK-зависимостей (users раньше attempts/hint_reveals) — дамп заливается
как есть, без выключения проверок внешних ключей.
"""
import sys
from datetime import datetime, timezone

from sqlalchemy import insert, select

from webapp.core import models  # noqa: F401  (регистрирует таблицы в Base.metadata)
from webapp.core.db import Base, engine


def render_insert(table, row: dict) -> str:
    """Скомпилировать INSERT для одной строки с литеральными значениями.

    literal_binds против диалекта движка даёт корректное экранирование
    строк/дат/NULL без ручной возни с кавычками.
    """
    stmt = insert(table).values(**row).compile(
        dialect=engine.dialect, compile_kwargs={"literal_binds": True}
    )
    return f"{stmt};"


def main() -> None:
    print("-- Дамп БД (INSERT-ы без схемы; таблицы создаёт create_all)")
    print(f"-- generated: {datetime.now(timezone.utc).isoformat()}")
    total = 0
    with engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            rows = [dict(row._mapping) for row in conn.execute(select(table))]
            print(f"\n-- {table.name}: {len(rows)} строк")
            for row in rows:
                print(render_insert(table, row))
            total += len(rows)
            print(f"{table.name}: {len(rows)} строк", file=sys.stderr)
    print(f"всего: {total} строк", file=sys.stderr)


if __name__ == "__main__":
    main()
