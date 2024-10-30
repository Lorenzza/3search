# Movie Reviews Search System

Система поиска по отзывам к фильмам с поддержкой различных методов поиска.

## Возможности

- Полнотекстовый поиск
- Векторный поиск
- Гибридный поиск
- REST API
- Метрики производительности
- Валидация результатов

## Установка
bash
Клонирование репозитория
git clone https://github.com/your-repo/movie-reviews-search.git
cd movie-reviews-search
Установка зависимостей
pip install -r requirements.txt
Инициализация индексов
python run_init_services.py
Запуск сервисов
python run_all_services.py

## Структура проекта
/
├── data/                      # Директория для сохранения индексов
│   ├── vector_index.pkl
│   └── documents.pkl
│
├── prepare_data/              # Модуль для подготовки данных
│   ├── __init__.py
│   ├── create_vector_index.py
│   ├── data_loader.py
│   └── init_elasticsearch.py
│
├── search_services/           # Модуль с поисковыми сервисами
│   ├── __init__.py
│   ├── fulltext/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── models.py
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── service.py
│   │   └── models.py
│   └── router/
│       ├── __init__.py
│       ├── service.py
│       └── models.py
│
├── run_init_services.py       # Инициализация данных
└── run_all_services.py        # Запуск сервисов

## Описание скриптов
run_init_services.py - выполняет долгую инициализацию данных:
- Создание векторного индекса
- Инициализация Elasticsearch
Запускается один раз при первом развертывании или обновлении данных
run_all_services.py - запускает поисковые сервисы:
- Проверяет наличие необходимых индексов
- Запускает сервисы поиска
Используется для ежедневной работы

## Особенности реализации:
- Единая точка входа на порту 8000
- Валидация входных параметров
- Асинхронные запросы к сервисам
- Гибридный поиск с нормализацией скоров
- Дедупликация результатов
- Подробные метрики


## Использование

См. [API документацию](docs/API.md) для подробной информации.

## Лицензия

MIT

