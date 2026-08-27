# API map: tutor-llm

Просканировано Python-файлов: 1
Включено в карту: 1
Пропущено без значимой API-информации: 0

Сводная статистика:
- модулей: 1
- классов: 1
- dataclass: 0
- функций: 3
- методов: 0
- констант: 4

---

# tutor-llm/main.py

Модуль:
Tutor-LLM — прокси к DeepSeek API для тьютора.

Живёт на роутере (как executor), доступен только внутри тоннеля
(порт 8011). Единственная задача: принять структурированный
запрос {task_context, student_code, question} от webapp'а на Frankfurt,
собрать промпт, сходить в DeepSeek, вернуть ответ. Ключ DEEPSEEK_API_KEY
живёт только в этом контейнере — наружу (во webapp, в браузер) не уходит.

В будущем здесь же вырастет RAG: добавится обращение к векторной БД,
промпт будет заземляться найденными чанками методики. Пока — чистый
LLM-вызов для проверки базовой связки end-to-end.

Константы:
- `DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')`
- `DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'`
- `DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')`
- `SYSTEM_PROMPT = 'Ты — тьютор по информатике (ОГЭ/ЕГЭ). Объясняешь ученику понятно, по делу, на русском. Если в вопр…`

Классы:

- `AskRequest(BaseModel)`
  Запрос от webapp'а. Все поля опциональны кроме question —
  тьютор может спрашивать и без контекста задачи.
  Поля:
  - `task_context: str | None = None`
  - `student_code: str | None = None`
  - `question: str`

Функции:

- `_build_user_message(req: AskRequest) -> str`
  Собирает пользовательское сообщение из структурированных полей.
  Разделители --- чтобы модели было проще различать блоки.

- `ask(payload: AskRequest)`
  Спросить DeepSeek: системный промпт репетитора + блоки задача/код/вопрос.
  Ошибки API и сети наружу отдаются как 502, отсутствие ключа — 500.

- `health()`
  Readiness-чек. Ключ НЕ отдаём наружу — только факт его наличия.