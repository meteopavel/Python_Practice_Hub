import ast
import logging
import os
import re

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from solvers import get_solver
from tasks_handlers import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TOKEN')


def extract_literals(text):
    text = re.sub(r'\s*;\s*', ';', text)
    parts = [part.strip() for part in text.split(';') if part.strip()]
    result = []
    for part in parts:
        try:
            obj = ast.literal_eval(part)
            result.append(obj)
        except:
            lists = re.findall(r'(\[[^]]*])', part)
            for lst in lists:
                try:
                    result.append(ast.literal_eval(lst))
                except:
                    pass
    return result


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_task' not in context.user_data:
        return
    user_input = update.message.text.strip()
    task_num = context.user_data['awaiting_task']
    objects = extract_literals(user_input)
    if len(objects) == 1:
        data = objects[0]
    else:
        data = objects
    result = get_solver(task_num)(data)
    await update.message.reply_text(f'💁‍♂️ Ответ: <code>{result}</code>', parse_mode='HTML')
    del context.user_data['awaiting_task']


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(rf'Привет {user.mention_html()}!',)


if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    for task_id, handler in task_handlers.items():
        application.add_handler(CommandHandler(f'task_{task_id}', handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)