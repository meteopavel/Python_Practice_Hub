import json


with open('tasks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

INPUT_HINTS = data['input_hints']

TASKS = {}
for k, v in data['tasks'].items():
    TASKS[int(k)] = v