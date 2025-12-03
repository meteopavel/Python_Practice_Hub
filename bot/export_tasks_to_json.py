import json
from constants import TASKS, INPUT_HINTS


data = {
    'input_hints': INPUT_HINTS,
    'tasks': TASKS
}

with open('tasks.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('✅ Константы успешно сохранены в tasks.json')