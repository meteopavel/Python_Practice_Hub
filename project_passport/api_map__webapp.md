# API map: webapp

Просканировано Python-файлов: 10
Включено в карту: 10
Пропущено без значимой API-информации: 0

Сводная статистика:
- модулей: 10
- классов: 9
- dataclass: 0
- функций: 53
- методов: 1
- констант: 18

---

# webapp/auth.py

Модуль:
Простая авторизация логин/пароль + сессия по подписанной cookie.
Ученики заводятся вручную (см. create_user.py) — самостоятельной регистрации нет.

Функции:

- `hash_password(password: str) -> str`
  Нет докстринга.

- `verify_password(password: str, password_hash: str) -> bool`
  Нет докстринга.

- `authenticate(db: Session, username: str, password: str) -> User | None`
  Нет докстринга.

- `current_user_id(request: Request) -> int | None`
  Нет докстринга.

- `current_user_role(request: Request) -> str | None`
  Нет докстринга.

- `unauthorized() -> JSONResponse`
  Нет докстринга.

- `forbidden() -> JSONResponse`
  Нет докстринга.

---

# webapp/bot_bridge.py

Модуль:
Мост к банку заданий и эталонных решений в bot/ — общий источник
для Telegram-бота и веб-грейдера, чтобы не дублировать содержимое.

Константы:
- `_BOT_DIR = Path(__file__).resolve().parent.parent / 'bot'`
- `TASKS = {int(k): v for (k, v) in _data['tasks'].items()}`

---

# webapp/create_user.py

Модуль:
Завести пользователя вручную (самостоятельной регистрации нет).

Использование (внутри контейнера app):
    docker exec -it python_practice_hub-app-1 python -m webapp.scripts.create_user <username> [role]

role: student (по умолчанию) | tutor

Спросит пароль интерактивно (не через argv — не светится в истории/логах/ps).

Константы:
- `VALID_ROLES = (ROLE_STUDENT, ROLE_TUTOR)`

Функции:

- `main() -> None`
  Нет докстринга.

---

# webapp/db.py

Модуль:
Подключение к БД: движок + фабрика сессий SQLAlchemy.

Константы:
- `DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./local.db')`

Функции:

- `get_db()`
  Нет докстринга.

---

# webapp/grading.py

Модуль:
Grading engine: сверяет код ученика с эталонным решением на курированных
тестовых входах. Это единственное место, где 'правильность' определяется —
через исполнение, а не через доверие к модели.

Сам код ученика здесь НЕ выполняется — это ушло в executor/ (отдельный
сервис на роутере, за тоннелем). Здесь только оркестрация: эталон + запрос
к исполнителю + сравнение.

Константы:
- `EXECUTOR_URL = os.environ.get('EXECUTOR_URL', 'http://127.0.0.1:8010')`

Классы:

- `ExecutorUnavailable(Exception)`
  Нет докстринга.

Функции:

- `_run_student_code(code: str, test_input) -> dict`
  Нет докстринга.

- `_normalize(value)`
  Эталон вызывается в процессе напрямую (без сериализации), а решение
  ученика приходит через JSON и тем самым теряет типы вроде tuple (JSON
  их не различает от list). Прогоняем эталон через тот же JSON-круглый
  обмен, чтобы сравнение было честным по обе стороны.

- `run_free(code: str) -> dict`
  Свободный запуск кода без сверки с эталоном — для подсказки, где
  тьютору нужно просто показать вывод print(), а не пройти тесты.

- `grade(task_id: int, code: str) -> dict`
  Нет докстринга.

---

# webapp/main.py

Модуль:
FastAPI-приложение веб-грейдера. Оболочка: отдаёт список заданий,
логин/сессию и принимает решение ученика. Вся логика проверки —
в grading.py/sandbox.py, вся модель данных — в models.py.

Константы:
- `SESSION_SECRET = os.environ.get('SESSION_SECRET')`
- `TURN_SECRET = os.environ.get('TURN_SECRET')`
- `TURN_URLS = os.environ.get('TURN_URLS')`
- `STUN_URLS = os.environ.get('STUN_URLS', 'stun:informatika.meteopavel.space:3478')`
- `TUTOR_LLM_URL = os.environ.get('TUTOR_LLM_URL', 'http://10.0.0.1:8011')`
- `STATIC_DIR = Path(__file__).resolve().parent / 'static'`

Классы:

- `SubmissionRequest(BaseModel)`
  Нет докстринга.
  Поля:
  - `task_id: int`
  - `code: str`

- `HintFreeRunRequest(BaseModel)`
  Нет докстринга.
  Поля:
  - `code: str`

- `TutorAskRequest(BaseModel)`
  Запрос тьютора к ИИ-помощнику. task_context/student_code опциональны —
  можно спросить и без них. question обязателен.
  Поля:
  - `task_context: str | None = None`
  - `student_code: str | None = None`
  - `question: str`

- `CreateStudentRequest(BaseModel)`
  Нет докстринга.
  Поля:
  - `username: str`
  - `password: str`

- `SetPasswordRequest(BaseModel)`
  Нет докстринга.
  Поля:
  - `password: str`

Функции:

- `create_tables()`
  Нет докстринга.

- `login_page()`
  Нет докстринга.

- `login_submit(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db))`
  Нет докстринга.

- `logout(request: Request)`
  Нет докстринга.

- `index(request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `tutor_page(request: Request)`
  Нет докстринга.

- `tutor_student_page(student_id: int, request: Request)`
  Нет докстринга.

- `start_impersonation(student_id: int, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `stop_impersonation(request: Request)`
  Нет докстринга.

- `materials_page(module: str, lesson: str, request: Request)`
  Нет докстринга.

- `effective_identity(request: Request, db: Session)`
  Для тьютора в режиме "посмотреть как ученик" подменяет личность только
  для student-facing данных (список заданий/свои попытки) — НЕ для
  авторизации, та остаётся на реальной роли из сессии.

- `list_tasks(request: Request)`
  Нет докстринга.

- `list_materials(request: Request)`
  Нет докстринга.

- `get_material(module: str, lesson: str, request: Request)`
  Нет докстринга.

- `get_solution(task_id: int, request: Request)`
  Нет докстринга.

- `turn_credentials(request: Request)`
  Нет докстринга.

- `me(request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `_task_status_map(db: Session, user_id: int) -> dict`
  task_id -> 'pass'/'fail' по всей истории попыток пользователя — 'pass'
  если хоть одна попытка когда-либо прошла. Общий код для своей истории
  (эффективная личность) и истории конкретного ученика (вид тьютора).

- `_task_attempts(db: Session, user_id: int, task_id: int) -> list`
  Нет докстринга.

- `my_attempts(request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `my_task_attempts(task_id: int, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `list_students(request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `create_student(payload: CreateStudentRequest, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `set_student_password(student_id: int, payload: SetPasswordRequest, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `_require_student(db: Session, student_id: int)`
  Нет докстринга.

- `student_task_status(student_id: int, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `student_task_attempts(student_id: int, task_id: int, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `session_ws(websocket: WebSocket, student_id: int)`
  Живая комната одного ученика: сам ученик + один или несколько тьюторов,
  которые сейчас смотрят его экран. Тьютор пишет — ученик видит подсказку,
  ученик печатает — тьютор видит код в реальном времени.

- `run_solve_code_free(payload: HintFreeRunRequest, request: Request)`
  Свободный запуск кода ученика в его собственном редакторе — без сверки
  с эталоном, чтобы можно было просто написать print(...) и посмотреть вывод.

- `submit(payload: SubmissionRequest, request: Request, db: Session = Depends(get_db))`
  Нет докстринга.

- `run_hint_code(payload: SubmissionRequest, request: Request)`
  Тьютор проверяет код прямо в редакторе подсказки — тот же grade(),
  но без записи Attempt: это демонстрация ученику, а не его попытка.

- `run_hint_code_free(payload: HintFreeRunRequest, request: Request)`
  Свободный запуск кода в подсказке — без сверки с эталоном, просто
  исполняет код как есть (print() и любые операторы отрабатывают).

- `tutor_ask(payload: TutorAskRequest, request: Request)`
  Тьютор спрашивает ИИ-помощника (DeepSeek через микросервис tutor-llm
  на роутере). Прокси: webapp не знает ключ DeepSeek, он только пересылает
  структурированный запрос в tutor-llm по внутренней сети (как executor).
  Только для роли tutor.

---

# webapp/materials.py

Модуль:
Справочные материалы — те же учебные ноутбуки (1_introduction/,
2_loops_and_conditions/ и т.д. в корне репозитория), что и раньше лежали
только как Jupyter-тетрадки. Здесь не БД и не отдельный конвертированный
формат — .ipynb читается напрямую (это просто JSON), один раз при старте
приложения, и держится в памяти. Ноутбуки маленькие (~470KB на все 36),
без картинок/attachments — только code-ячейки, объяснение зашито в них
как строки-докстринги. Собственный парсер вместо nbconvert: контента
слишком мало и однообразно, чтобы тащить чужой шаблон/CSS, который потом
пришлось бы перекраивать под дизайн-систему сайта.

Константы:
- `_ROOT = Path(__file__).resolve().parent.parent`
- `_MODULE_TITLES = {'1_introduction': 'Введение', '2_loops_and_conditions': 'Циклы и условия', '3_functions': 'Функции…`
- `_TITLE_OVERRIDES = {('1_introduction', '0_venv_install'): 'Установка и работа с venv', ('1_introduction', '1_intro'): …`
- `_NUM_PREFIX = re.compile('^(\\d+)_')`

Функции:

- `_sort_key(filename: str) -> tuple`
  Нет докстринга.

- `_extract_title(module: str, slug: str, first_cell_source: str) -> str`
  Нет докстринга.

- `_load_notebook(path: Path) -> list`
  Возвращает список ячеек: [{"code": str, "output": str|None, "is_error": bool}].

- `_build_manifest()`
  Нет докстринга.

- `get_lesson(module: str, slug: str)`
  Нет докстринга.

---

# webapp/models.py

Модуль:
Модели: пользователи (ученики и репетитор, заводятся вручную) и попытки решения.

Константы:
- `ROLE_STUDENT = 'student'`
- `ROLE_TUTOR = 'tutor'`

Классы:

- `User(Base)`
  Нет докстринга.

- `Attempt(Base)`
  Нет докстринга.

---

# webapp/realtime.py

Модуль:
In-memory realtime-комнаты для живых сессий тьютор-ученик.

Комната = один ученик. Состояние живёт, пока жив процесс приложения — рестарт
контейнера просто обнуляет текущие live-сессии, и это ожидаемо: это сиюминутное
состояние (кто сейчас печатает), а не история попыток (та в БД).

Классы:

- `Room`
  Нет докстринга.
  Методы:
  - `__init__(self)`
    Нет докстринга.

Функции:

- `get_room(student_id: int) -> Room`
  Нет докстринга.

- `safe_send(websocket: WebSocket, payload: dict) -> None`
  Отправка соседу по комнате не должна ронять цикл отправителя, если
  сосед уже отвалился, а disconnect ещё не долетел до finally.

---

# webapp/test_cases.py

Модуль:
Курированные тестовые входы для веб-грейдера.

Ключ — номер задания (совпадает с TASKS в bot/constants.py), значение —
список входов, на которых код ученика сверяется с эталонным решением
(solve_task_N из bot/solvers.py). Задание доступно в веб-грейдере тогда
и только тогда, когда для него здесь заведены тестовые входы — это и есть
курируемая база, а не автогенерация вслепую.

Задание 47 (НОК) до 2026-07-21 было исключено отсюда: в bot/solvers.py у
solve_task_47 было перепутано сравнение (data[0] % max_delim вместо
max_delim % data[0]) — цикл while True никогда не завершался для двух
разных положительных чисел, без таймаута на стороне эталона это вешало
процесс приложения насмерть при первой же проверке. Исправлено, задание
включено обратно.

Константы:
- `TEST_CASES = {1: [[3, 2, 2, 1, 5, 3], [1, 1, 1], [4, 4, 4, 2, 1, 2]], 2: [[1, 2, 3, 4, 5, 6], [1, 3, 5], [0, -2,…`