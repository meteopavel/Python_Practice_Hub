# -*- coding: utf-8 -*-
"""Завести пользователя вручную (самостоятельной регистрации нет).

Использование (внутри контейнера app, WORKDIR=/app):
    docker exec -it python_practice_hub-app-1 python -m webapp.scripts.create_user <username> [role]

role: student (по умолчанию) | tutor

Спросит пароль интерактивно (не через argv — не светится в истории/логах/ps).
"""
import getpass
import sys

from webapp.core.auth import hash_password, password_policy_error
from webapp.core.db import SessionLocal
from webapp.core.models import ROLE_STUDENT, ROLE_TUTOR, User

VALID_ROLES = (ROLE_STUDENT, ROLE_TUTOR)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print(f"Использование: python -m webapp.scripts.create_user <username> [{'|'.join(VALID_ROLES)}]")
        sys.exit(1)

    username = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) == 3 else ROLE_STUDENT
    if role not in VALID_ROLES:
        print(f"Неизвестная роль '{role}', допустимо: {', '.join(VALID_ROLES)}")
        sys.exit(1)

    password = getpass.getpass("Пароль: ")
    password_repeat = getpass.getpass("Повтори пароль: ")
    if password != password_repeat:
        print("Пароли не совпадают")
        sys.exit(1)
    if (policy_error := password_policy_error(password)) is not None:
        print(policy_error)
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            print(f"Пользователь '{username}' уже существует")
            sys.exit(1)
        user = User(username=username, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
        print(f"✅ Пользователь '{username}' ({role}) создан (id={user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
