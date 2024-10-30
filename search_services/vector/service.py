from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from search_services import VECTOR_CONFIG
import numpy as np
from prepare_data.data_loader import load_index_and_documents
from .models import SearchRequest, SearchResponse, SearchResult
import time

app = FastAPI(title="Vector Search Service")

class VectorSearchService:
    def __init__(self):
        self.model = None
        self.index = None
        self.documents = None
        self.initialize_service()

    def initialize_service(self):
        """Инициализация сервиса"""
        try:
            # Загрузка модели
            model_name = 'distiluse-base-multilingual-cased-v2'
            print(f"Загрузка модели: {model_name}")
            self.model = SentenceTransformer(model_name)

            # Загрузка индекса и документов
            print("Загрузка индекса и документов...")
            self.index, self.documents = load_index_and_documents()
            
            print("Сервис успешно инициализирован")
            print(f"- Размерность векторов: {self.index.d}")
            print(f"- Количество документов: {len(self.documents)}")

        except Exception as e:
            print(f"Ошибка при инициализации сервиса: {str(e)}")
            raise

    async def search(self, query: str, top_k: int = 5) -> SearchResponse:
        """Выполняет векторный поиск"""
        start_time = time.time()
        
        try:
            # Векторизация запроса
            query_vector = self.model.encode([query])[0]
            query_vector = query_vector.reshape(1, -1).astype('float32')

            # Поиск ближайших векторов
            distances, indices = self.index.search(query_vector, top_k)
            
            # Формирование результатов
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                doc = self.documents[idx]
                similarity = 1 / (1 + distance)  # Преобразование расстояния в сходство
                results.append(
                    SearchResult(
                        movie_id=doc["movie_id"],
                        similarity=float(similarity),
                        content=doc["content"]
                    )
                )

            # Метрики ранжирования
            ranking_metrics = {
                "max_similarity": float(max(1 / (1 + distances[0]))),
                "average_similarity": float(np.mean(1 / (1 + distances[0]))),
                "latency": round(time.time() - start_time, 3)
            }

            return SearchResponse(results=results, ranking_metrics=ranking_metrics)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при выполнении поиска: {str(e)}"
            )

# Создание экземпляра сервиса
service = VectorSearchService()

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Endpoint для векторного поиска"""
    return await service.search(request.query, request.top_k)

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "index_size": service.index.ntotal if service.index else 0,
        "documents_count": len(service.documents) if service.documents else 0
    }

def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)