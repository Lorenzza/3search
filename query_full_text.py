import requests
import json

# URL вашего сервиса
url = "http://127.0.0.1:8001/search"

# Данные запроса
payload = {
    "query": "Фильм про зелёную милю",
    "top_k": 5
}

# Отправка POST-запроса
response = requests.post(url, json=payload)

# Проверка статуса ответа
if response.status_code == 200:
    # Успешный ответ
    results = response.json()
    print(json.dumps(results, ensure_ascii=False, indent=2))
else:
    # Ошибка
    print(f"Ошибка: {response.status_code}")
    print(response.text)