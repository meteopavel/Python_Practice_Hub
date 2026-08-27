# API map: bot

Просканировано Python-файлов: 6
Включено в карту: 6
Пропущено без значимой API-информации: 0

Сводная статистика:
- модулей: 6
- классов: 0
- dataclass: 0
- функций: 126
- методов: 0
- констант: 5

---

# bot/bot.py

Модуль:
Легаси Telegram-бот «задача → ответ»: команда /task_N выдаёт условие,
следующее сообщение ученика парсится как вход и прогоняется через эталон.
Проект начинался с него; продукт теперь — веб-грейдер (webapp/), но банк
заданий (tasks.json, solvers.py) общий для обоих контуров.

Константы:
- `TOKEN = os.getenv('TOKEN')`

Функции:

- `extract_literals(text)`
  Разобрать ввод ученика: питоновские литералы через ';' (или списки,
  вытащенные из свободного текста).

- `handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE)`
  Ответ на данные ждущего задания: разобрать вход, прогнать эталон,
  прислать ответ (диалог одноразовый — ожидание сбрасывается).

- `start(update: Update, context: ContextTypes.DEFAULT_TYPE)`
  Приветствие на /start.

---

# bot/constants.py

Модуль:
Банк заданий — ИСТОЧНИК для генератора export_tasks_to_json.py, который
упаковывает TASKS/INPUT_HINTS в bot/tasks.json.

Константы:
- `INPUT_HINTS = {'number': 'Введите число в формате:', 'word': 'Введите слово в формате:', 'list_of_numbers': 'Введ…`
- `TASKS = {1: {'description': 'Удалить дубликаты из списка, сохранив порядок.', 'example': '[3, 2, 2, 1, 5, 3…`

---

# bot/export_tasks_to_json.py

Модуль:
Перегенерировать bot/tasks.json из constants.py — запускать после каждой
правки банка заданий (подробности — в шапке constants.py).

---

# bot/load_tasks_from_json.py

Модуль:
Загрузка банка заданий из tasks.json — единый источник и для бота, и для
webapp (через grading/bot_bridge.py).

Константы:
- `INPUT_HINTS = data['input_hints']`
- `TASKS = {}`

---

# bot/solvers.py

Модуль:
Эталонные решения всех заданий: solve_task_N(data) → эталонный ответ,
get_solver(task_num) — диспетчер. Это генерируемый банк данных, а не API —
докстринги на каждой solve_task_* не нужны (их 121+).

Функции:

- `get_solver(task_num)`
  Нет докстринга.

- `solve_task_1(data)`
  Нет докстринга.

- `solve_task_2(data)`
  Нет докстринга.

- `solve_task_3(data)`
  Нет докстринга.

- `solve_task_4(data)`
  Нет докстринга.

- `solve_task_5(data)`
  Нет докстринга.

- `solve_task_6(data)`
  Нет докстринга.

- `solve_task_7(data)`
  Нет докстринга.

- `solve_task_8(data)`
  Нет докстринга.

- `solve_task_9(data)`
  Нет докстринга.

- `solve_task_10(data)`
  Нет докстринга.

- `solve_task_11(data)`
  Нет докстринга.

- `solve_task_12(data)`
  Нет докстринга.

- `solve_task_13(data)`
  Нет докстринга.

- `solve_task_14(data)`
  Нет докстринга.

- `solve_task_15(data)`
  Нет докстринга.

- `solve_task_16(data)`
  Нет докстринга.

- `solve_task_17(data)`
  Нет докстринга.

- `solve_task_18(data)`
  Нет докстринга.

- `solve_task_19(data)`
  Нет докстринга.

- `solve_task_20(data)`
  Нет докстринга.

- `solve_task_21(data)`
  Нет докстринга.

- `solve_task_22(data)`
  Нет докстринга.

- `solve_task_23(data)`
  Нет докстринга.

- `solve_task_24(data)`
  Нет докстринга.

- `solve_task_25(data)`
  Нет докстринга.

- `solve_task_26(data)`
  Нет докстринга.

- `solve_task_27(data)`
  Нет докстринга.

- `solve_task_28(data)`
  Нет докстринга.

- `solve_task_29(data)`
  Нет докстринга.

- `solve_task_30(data)`
  Нет докстринга.

- `solve_task_31(data)`
  Нет докстринга.

- `solve_task_32(data)`
  Нет докстринга.

- `solve_task_33(data)`
  Нет докстринга.

- `solve_task_34(data)`
  Нет докстринга.

- `solve_task_35(data)`
  Нет докстринга.

- `solve_task_36(data)`
  Нет докстринга.

- `solve_task_37(data)`
  Нет докстринга.

- `solve_task_38(data)`
  Нет докстринга.

- `solve_task_39(data)`
  Нет докстринга.

- `solve_task_40(data)`
  Нет докстринга.

- `solve_task_41(data)`
  Нет докстринга.

- `solve_task_42(data)`
  Нет докстринга.

- `solve_task_43(data)`
  Нет докстринга.

- `solve_task_44(data)`
  Нет докстринга.

- `solve_task_45(data)`
  Нет докстринга.

- `solve_task_46(data)`
  Нет докстринга.

- `solve_task_47(data)`
  Нет докстринга.

- `solve_task_48(data)`
  Нет докстринга.

- `solve_task_49(data)`
  Нет докстринга.

- `solve_task_50(data)`
  Нет докстринга.

- `solve_task_51(data)`
  Нет докстринга.

- `solve_task_52(data)`
  Нет докстринга.

- `solve_task_53(data)`
  Нет докстринга.

- `solve_task_54(data)`
  Нет докстринга.

- `solve_task_55(data)`
  Нет докстринга.

- `solve_task_56(data)`
  Нет докстринга.

- `solve_task_57(data)`
  Нет докстринга.

- `solve_task_58(data)`
  Нет докстринга.

- `solve_task_59(data)`
  Нет докстринга.

- `solve_task_60(data)`
  Нет докстринга.

- `solve_task_61(data)`
  Нет докстринга.

- `solve_task_62(data)`
  Нет докстринга.

- `solve_task_63(data)`
  Нет докстринга.

- `solve_task_64(data)`
  Нет докстринга.

- `solve_task_65(data)`
  Нет докстринга.

- `solve_task_66(data)`
  Нет докстринга.

- `solve_task_67(data)`
  Нет докстринга.

- `solve_task_68(data)`
  Нет докстринга.

- `solve_task_69(data)`
  Нет докстринга.

- `solve_task_70(data)`
  Нет докстринга.

- `solve_task_71(data)`
  Нет докстринга.

- `solve_task_72(data)`
  Нет докстринга.

- `solve_task_73(data)`
  Нет докстринга.

- `solve_task_74(data)`
  Нет докстринга.

- `solve_task_75(data)`
  Нет докстринга.

- `solve_task_76(data)`
  Нет докстринга.

- `solve_task_77(data)`
  Нет докстринга.

- `solve_task_78(data)`
  Нет докстринга.

- `solve_task_79(data)`
  Нет докстринга.

- `solve_task_80(data)`
  Нет докстринга.

- `solve_task_81(data)`
  Нет докстринга.

- `solve_task_82(data)`
  Нет докстринга.

- `solve_task_83(data)`
  Нет докстринга.

- `solve_task_84(data)`
  Нет докстринга.

- `solve_task_85(data)`
  Нет докстринга.

- `solve_task_86(data)`
  Нет докстринга.

- `solve_task_87(data)`
  Нет докстринга.

- `solve_task_88(data)`
  Нет докстринга.

- `solve_task_89(data)`
  Нет докстринга.

- `solve_task_90(data)`
  Нет докстринга.

- `solve_task_91(data)`
  Нет докстринга.

- `solve_task_92(data)`
  Нет докстринга.

- `solve_task_93(data)`
  Нет докстринга.

- `solve_task_94(data)`
  Нет докстринга.

- `solve_task_95(data)`
  Нет докстринга.

- `solve_task_96(data)`
  Нет докстринга.

- `solve_task_97(data)`
  Нет докстринга.

- `solve_task_98(data)`
  Нет докстринга.

- `solve_task_99(data)`
  Нет докстринга.

- `solve_task_100(data)`
  Нет докстринга.

- `solve_task_101(data)`
  Нет докстринга.

- `solve_task_102(data)`
  Нет докстринга.

- `solve_task_103(data)`
  Нет докстринга.

- `solve_task_104(data)`
  Нет докстринга.

- `solve_task_105(data)`
  Нет докстринга.

- `solve_task_106(data)`
  Нет докстринга.

- `solve_task_107(data)`
  Нет докстринга.

- `solve_task_108(data)`
  Нет докстринга.

- `solve_task_109(data)`
  Нет докстринга.

- `solve_task_110(data)`
  Нет докстринга.

- `solve_task_111(data)`
  Нет докстринга.

- `solve_task_112(data)`
  Нет докстринга.

- `solve_task_113(data)`
  Нет докстринга.

- `solve_task_114(data)`
  Нет докстринга.

- `solve_task_115(data)`
  Нет докстринга.

- `solve_task_116(data)`
  Нет докстринга.

- `solve_task_117(data)`
  Нет докстринга.

- `solve_task_118(data)`
  Нет докстринга.

- `solve_task_119(data)`
  Нет докстринга.

- `solve_task_120(data)`
  Нет докстринга.

- `solve_task_0(data)`
  Нет докстринга.

---

# bot/tasks_handlers.py

Модуль:
Хендлеры команд /task_N: фабрика собирает их из банка TASKS в tasks.json
(по одному хендлеру на задание, регистрируются в bot.py).

Функции:

- `make_task_handler(task_num)`
  Хендлер /task_N: показать условие, формат входа и пример; перевести
  диалог в режим ожидания данных (awaiting_task).