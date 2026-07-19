# -*- coding: utf-8 -*-
"""Завести ученика вручную (самостоятельной регистрации нет).

Использование (внутри контейнера app):
    docker exec -it python_practice_hub-app-1 python create_user.py <username>

Спросит пароль интерактивно (не через argv — не светится в истории/логах/ps).
"""
import getpass
import sys

from auth import hash_password
from db import SessionLocal
from models import User


def main() -> None:
    if len(sys.argv) != 2:
        print("Использование: python create_user.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    password = getpass.getpass("Пароль: ")
    password_repeat = getpass.getpass("Повтори пароль: ")
    if password != password_repeat:
        print("Пароли не совпадают")
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            print(f"Пользователь '{username}' уже существует")
            sys.exit(1)
        user = User(username=username, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"✅ Пользователь '{username}' создан (id={user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
