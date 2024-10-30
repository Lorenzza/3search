from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import numpy as np
import math
import logging
from .models import RouterRequest, RouterResponse, SearchResult, SearchMethod

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    app.state.router = SearchRouter()
    yield
    # Очистка при завершении
    await app.state.router.close()

app = FastAPI(title="Search Router Service", lifespan=lifespan)

class SearchRouter:
    def __init__(self):
        self.fulltext_url = "http://127.0.0.1:8001/search"
        self.vector_url = "http://127.0.0.1:8002/search"
        self.client = httpx.AsyncClient()

    async def close(self):
        """Закрытие клиента при завершении работы"""
        await self.client.aclose()

    async def fulltext_search(self, query: str, top_k: int):
        """Полнотекстовый поиск"""
        try:
            response = await self.client.post(
                self.fulltext_url,
                json={"query": query, "top_k": top_k}
            )
            response.raise_for_status()
            data = response.json()
            return [
                SearchResult(
                    movie_id=r["movie_id"],
                    score=r["score"],
                    content=r["content"],
                    source="fulltext"
                )
                for r in data["results"]
            ], data["metrics"]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка полнотекстового поиска: {str(e)}"
            )
    async def vector_search(self, query: str, top_k: int):
        """Векторный поиск"""
        try:
            response = await self.client.post(
                self.vector_url,
                json={"query": query, "top_k": top_k}
            )
            response.raise_for_status()
            data = response.json()
            
            # Создаем метрики самостоятельно, так как их нет в ответе
            metrics = {
                "latency": data.get("latency", 0),
                "total_results": len(data["results"]),
                "max_similarity": max(r["similarity"] for r in data["results"]) if data["results"] else 0,
                "average_similarity": sum(r["similarity"] for r in data["results"]) / len(data["results"]) if data["results"] else 0
            }
            
            results = [
                SearchResult(
                    movie_id=r["movie_id"],
                    score=r["similarity"],
                    content=r["content"],
                    source="vector"
                )
                for r in data["results"]
            ]
            
            return results, metrics
        except Exception as e:
            logger.error(f"Ошибка векторного поиска: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка векторного поиска: {str(e)}"
            )

    async def hybrid_search(self, query: str, top_k: int):
        """Гибридный поиск"""
        try:
            # Запускаем оба поиска параллельно
            fulltext_future = self.fulltext_search(query, top_k)
            vector_future = self.vector_search(query, top_k)
            
            fulltext_results, fulltext_metrics = await fulltext_future
            vector_results, vector_metrics = await vector_future
            
            # Нормализация скоров
            all_results = fulltext_results + vector_results
            all_scores = [r.score for r in all_results]
            max_score = max(all_scores) if all_scores else 0

            for r in all_results:
                # Используем формулу нормализации
                normalized = 1 / (1 + math.exp(-r.score/max_score))
                normalized = (normalized - 0.5) * 2 + 0.4
                r.score = max(0, min(1, normalized))

            # Сортировка и дедупликация по movie_id
            seen_movies = set()
            unique_results = []
            for r in sorted(all_results, key=lambda x: x.score, reverse=True):
                if r.movie_id not in seen_movies:
                    seen_movies.add(r.movie_id)
                    r.source = "hybrid"
                    unique_results.append(r)

            # Объединение метрик
            hybrid_metrics = {
                "max_similarity": max(r.score for r in unique_results) if unique_results else 0,
                "average_similarity": sum(r.score for r in unique_results) / len(unique_results) if unique_results else 0,
                "total_results": len(unique_results),
                "latency": max(
                    fulltext_metrics["latency"],
                    vector_metrics["latency"]
                )
            }
            
            return unique_results[:top_k], hybrid_metrics

        except Exception as e:
            logger.error(f"Ошибка в гибридном поиске: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка гибридного поиска: {str(e)}"
            )

    async def search(self, request: RouterRequest) -> RouterResponse:
        """Выполнение поиска выбранным методом"""
        if request.method == SearchMethod.FULLTEXT:
            results, metrics = await self.fulltext_search(request.query, request.top_k)
        elif request.method == SearchMethod.VECTOR:
            results, metrics = await self.vector_search(request.query, request.top_k)
        else:  # HYBRID
            results, metrics = await self.hybrid_search(request.query, request.top_k)

        return RouterResponse(results=results, metrics=metrics)

@app.post("/search", response_model=RouterResponse)
async def search(request: RouterRequest):
    """Единая точка входа для всех типов поиска"""
    return await app.state.router.search(request)