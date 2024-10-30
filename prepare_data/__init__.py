from pathlib import Path

# Базовые пути
BASE_DATA_PATH = Path(r"D:\_DS\test_q\transneft\DATA\RAW\dataset")
OUTPUT_PATH = Path(r"D:\_DS\test_q\transneft\data")

# Убедимся, что директория существует
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# Константы
FOLDERS = ["neg", "neu", "pos"]
MODEL_NAME = 'distiluse-base-multilingual-cased-v2'

# Elasticsearch настройки
ELASTICSEARCH_CONFIG = {
    "user": "elastic",
    "password": "As7VBZe1Je5FdveBhd3m",
    "url": "http://localhost:9200",
    "index_name": "movie_reviews",
    "batch_size": 1000
}