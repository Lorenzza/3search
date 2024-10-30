import requests
import json
from typing import List, Dict
import asyncio
import aiohttp

class SearchResult:
    def __init__(self, movie_id: str, content: str, similarity: float):
        self.movie_id = movie_id
        self.content = content
        self.similarity = similarity

async def perform_search(session: aiohttp.ClientSession, url: str, query: str, top_k: int) -> List[Dict]:
    """Выполняет поисковый запрос к указанному сервису"""
    try:
        async with session.post(url, json={"query": query, "top_k": top_k}) as response:
            response.raise_for_status()
            return (await response.json())["results"]
    except Exception as e:
        print(f"Ошибка при запросе к {url}: {e}")
        return []

async def hybrid_search(query: str, top_k: int = 5):
    """Выполняет гибридный поиск, объединяя результаты полнотекстового и векторного поиска"""
    fulltext_url = "http://127.0.0.1:8001/search"
    vector_url = "http://127.0.0.1:8002/search"
    
    # Веса для комбинирования результатов
    fulltext_weight = 0.6
    vector_weight = 1 - fulltext_weight
    
    async with aiohttp.ClientSession() as session:
        # Выполняем запросы параллельно
        fulltext_results, vector_results = await asyncio.gather(
            perform_search(session, fulltext_url, query, top_k),
            perform_search(session, vector_url, query, top_k)
        )

    # Объединяем результаты
    combined_results = {}
    
    # Добавляем результаты полнотекстового поиска
    for result in fulltext_results:
        movie_id = result["movie_id"]
        combined_results[movie_id] = {
            "movie_id": movie_id,
            "content": result.get("snippet", ""),
            "similarity": result["similarity"] * fulltext_weight,
            "sources": ["fulltext"]
        }

    # Добавляем результаты векторного поиска
    for result in vector_results:
        movie_id = result["movie_id"]
        if movie_id in combined_results:
            # Если документ уже есть, добавляем взвешенную similarity
            combined_results[movie_id]["similarity"] += result["similarity"] * vector_weight
            combined_results[movie_id]["sources"].append("vector")
        else:
            # Если документ новый, добавляем его
            combined_results[movie_id] = {
                "movie_id": movie_id,
                "content": result.get("content", ""),
                "similarity": result["similarity"] * vector_weight,
                "sources": ["vector"]
            }

    # Сортируем результаты по убыванию similarity
    sorted_results = sorted(
        combined_results.values(),
        key=lambda x: x["similarity"],
        reverse=True
    )[:top_k]

    # Вычисляем метрики
    similarities = [result["similarity"] for result in sorted_results]
    metrics = {
        "average_similarity": sum(similarities) / len(similarities) if similarities else 0,
        "max_similarity": max(similarities) if similarities else 0,
        "min_similarity": min(similarities) if similarities else 0,
        "total_results": len(sorted_results)
    }

    return sorted_results, metrics

def print_results(results: List[Dict], metrics: Dict):
    """Выводит результаты поиска и метрики"""
    print("\nРезультаты гибридного поиска:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Movie ID: {result['movie_id']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Sources: {', '.join(result['sources'])}")
        print(f"Content: {result['content'][:150]}...")
    
    print("\nМетрики поиска:")
    print("-" * 80)
    for metric, value in metrics.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")

async def main():
    query = "Фильм про зелёную милю"
    top_k = 5
    
    try:
        results, metrics = await hybrid_search(query, top_k)
        print_results(results, metrics)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())