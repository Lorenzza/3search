import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Загрузка модели
model_name = 'distiluse-base-multilingual-cased-v2'  # Модель, поддерживающая русский язык
model = SentenceTransformer(model_name)

# URL вашего сервиса
url = "http://127.0.0.1:8002/search"

# Текстовый запрос
query_text = "Фильм про зелёную милю"

# Векторизация поискового запроса
query_vector = model.encode([query_text], convert_to_numpy=True).tolist()[0]  # Преобразуем в список для JSON

# Данные запроса
payload = {
    "query_vector": query_vector,
    "top_k": 10
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