"""Хендлеры команд /task_N: фабрика собирает их из банка TASKS в tasks.json
(по одному хендлеру на задание, регистрируются в bot.py)."""
from telegram import Update
from telegram.ext import ContextTypes

from load_tasks_from_json import INPUT_HINTS, TASKS


def make_task_handler(task_num):
    """Хендлер /task_N: показать условие, формат входа и пример; перевести
    диалог в режим ожидания данных (awaiting_task)."""
    async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        task = TASKS[task_num]
        input_type = task['type']
        input_hint = INPUT_HINTS[input_type]
        example_input = task['example'].split('→')[0].strip()
        await update.message.reply_text(
            f'📝 <b>Задача {task_num}:</b>\n{task["description"]}\n'
            f'Пример: {task["example"]}\n\n'
            f'{input_hint}\n'
            f'<code>{example_input}</code>',
            parse_mode='HTML'
        )
        context.user_data['awaiting_task'] = task_num
    return task_handler


task_handlers = {}
for task_num in TASKS:
    task_handlers[task_num] = make_task_handler(task_num)
