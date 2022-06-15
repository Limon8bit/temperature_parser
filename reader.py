import json

with open('./json/moscow.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    print(data)