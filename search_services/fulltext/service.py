from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
import logging
from contextlib import asynccontextmanager
import math
from search_services.config import ES_CONFIG, SEARCH_SETTINGS
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    method: int = 1


class FulltextSearchService:
    def __init__(self):
        """Инициализация сервиса полнотекстового поиска"""
        try:
            logger.info(f"Попытка подключения к Elasticsearch: {ES_CONFIG['host']}:{ES_CONFIG['port']}")
            
            self.es = Elasticsearch(
                f"http://{ES_CONFIG['host']}:{ES_CONFIG['port']}",
                basic_auth=(ES_CONFIG['user'], ES_CONFIG['password']),
                verify_certs=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Проверяем подключение
            if not self.es.ping():
                raise Exception(f"Не удалось подключиться к Elasticsearch по адресу {ES_CONFIG['host']}:{ES_CONFIG['port']}")
                
            info = self.es.info()
            logger.info(f"Сервис успешно инициализирован\n"
                       f"- Elasticsearch версия: {info['version']['number']}\n"
                       f"- Количество документов: {self.get_doc_count()}\n"
                       f"- URL: http://{ES_CONFIG['host']}:{ES_CONFIG['port']}")
        except Exception as e:
            logger.error(f"Ошибка инициализации Elasticsearch: {str(e)}")
            raise

    def get_doc_count(self) -> int:
        """Получение количества документов в индексе"""
        try:
            return self.es.count(index=ES_CONFIG["index_name"])["count"]
        except Exception:
            return 0

    def normalize_score(self, score: float, max_score: float) -> float:
        """
        Нормализация скора Elasticsearch в диапазон [0, 1]
        
        Args:
            score (float): Исходный скор
            max_score (float): Максимальный скор в результатах
        
        Returns:
            float: Нормализованный скор в диапазоне [0, 1]
        """
        if max_score == 0:
            return 0
        
        # Нормализация через сигмоиду
        normalized = 1 / (1 + math.exp(-score/max_score))
        
        # Приведение к диапазону [0, 1]
        normalized = (normalized - 0.5) * 2 + 0.4
        
        # Обрезка значений
        return max(0, min(1, normalized))

    async def search(self, query: str, top_k: int = 5):
        """
        Выполнение полнотекстового поиска
        
        Args:
            query (str): Поисковый запрос
            top_k (int): Количество результатов
        
        Returns:
            tuple: (список результатов, метрики поиска)
        """
        try:
            # Формирование поискового запроса
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "movie_id"],
                        "type": "best_fields",
                        "operator": "or",
                        "minimum_should_match": "70%"
                    }
                },
                "size": top_k,
                "_source": ["movie_id", "content"],
                "min_score": SEARCH_SETTINGS["min_score"],
                "timeout": SEARCH_SETTINGS["timeout"]
            }

            # Выполнение поиска
            response = self.es.search(
                index=ES_CONFIG["index_name"],
                body=search_body
            )

            max_score = response['hits']['max_score'] or 0
            
            # Формирование результатов
            results = []
            for hit in response['hits']['hits']:
                normalized_score = self.normalize_score(hit['_score'], max_score)
                results.append({
                    "movie_id": hit['_source']['movie_id'],
                    "content": hit['_source']['content'],
                    "score": normalized_score,
                    "source": "fulltext"
                })

            # Сбор метрик
            metrics = {
                "max_similarity": max(r['score'] for r in results) if results else 0,
                "average_similarity": sum(r['score'] for r in results) / len(results) if results else 0,
                "latency": response['took'] / 1000,  # мс -> сек
                "total_results": response['hits']['total']['value']
            }

            return results, metrics

        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка поиска: {str(e)}"
            )

    async def close(self):
        """Закрытие соединения с Elasticsearch"""
        try:
            await self.es.close()
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения: {str(e)}")

# Создание FastAPI приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    app.state.search_service = FulltextSearchService()
    yield
    # Очистка при завершении
    await app.state.search_service.close()

app = FastAPI(
    title="Fulltext Search Service",
    description="Сервис полнотекстового поиска на базе Elasticsearch",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/search")
async def search(request: SearchRequest):
    """
    Endpoint для выполнения полнотекстового поиска
    
    Args:
        request: SearchRequest с параметрами поиска
    
    Returns:
        dict: Результаты поиска и метрики
    """
    results, metrics = await app.state.search_service.search(
        query=request.query,
        top_k=request.top_k
    )
    return {
        "results": results,
        "metrics": metrics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)