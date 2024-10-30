from pathlib import Path

# Конфигурация Elasticsearch
ES_CONFIG = {
    "host": "localhost",
    "port": 9200,
    "user": "elastic",
    "password": "As7VBZe1Je5FdveBhd3m",
    "index_name": "movie_reviews"
}

# Настройки поиска Elasticsearch
SEARCH_SETTINGS = {
    "min_score": 0.1,
    "timeout": "30s"
}

# Конфигурация для векторного поиска
VECTOR_CONFIG = {
    "model_name": 'distiluse-base-multilingual-cased-v2',
    "data_dir": Path("data")
}