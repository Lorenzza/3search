from elasticsearch import Elasticsearch
import logging
from pathlib import Path
from search_services.config import ES_CONFIG  # Обновленный импорт

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_index(es: Elasticsearch) -> None:
    """Создание индекса с настройками"""
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "custom_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop", "snowball"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "movie_id": {"type": "keyword"},
                "review_id": {"type": "keyword"},
                "sentiment": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "custom_analyzer"}
            }
        }
    }

    if es.indices.exists(index=ES_CONFIG['index_name']):
        logger.info(f"Удаление существующего индекса {ES_CONFIG['index_name']}")
        es.indices.delete(index=ES_CONFIG['index_name'])
    
    logger.info(f"Создание индекса {ES_CONFIG['index_name']}")
    es.indices.create(index=ES_CONFIG['index_name'], body=index_settings)

def index_documents(es: Elasticsearch, base_path: Path) -> None:
    """Индексация документов"""
    folders = ["neg", "neu", "pos"]
    batch_size = 1000
    batch = []

    for folder in folders:
        folder_path = base_path / folder
        logger.info(f"Обработка папки: {folder}")
        
        for file_path in folder_path.glob("*.txt"):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                movie_id, review_id = file_path.stem.split('-')
                doc = {
                    "movie_id": movie_id,
                    "review_id": review_id,
                    "sentiment": folder,
                    "content": content
                }
                batch.append(doc)

                if len(batch) >= batch_size:
                    bulk_data = []
                    for doc in batch:
                        bulk_data.extend([
                            {"index": {"_index": ES_CONFIG['index_name']}},
                            doc
                        ])
                    es.bulk(body=bulk_data)
                    logger.info(f"Проиндексировано {len(batch)} документов")
                    batch = []

    if batch:
        bulk_data = []
        for doc in batch:
            bulk_data.extend([
                {"index": {"_index": ES_CONFIG['index_name']}},
                doc
            ])
        es.bulk(body=bulk_data)
        logger.info(f"Проиндексировано {len(batch)} документов")

def main():
    try:
        es = Elasticsearch(
            f"http://{ES_CONFIG['host']}:{ES_CONFIG['port']}",
            basic_auth=(ES_CONFIG['user'], ES_CONFIG['password']),
            verify_certs=False
        )

        if not es.ping():
            raise ConnectionError("Не удалось подключиться к Elasticsearch")

        logger.info(f"Подключено к Elasticsearch {es.info()['version']['number']}")
        
        create_index(es)
        
        base_path = Path("DATA/RAW/dataset")
        index_documents(es, base_path)
        
        logger.info("Индексация завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        raise
    finally:
        es.close()

if __name__ == "__main__":
    main()