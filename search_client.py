import argparse
import httpx
import json
import sys
from typing import Dict, Any
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, top_k: int = 5, method: int = 1) -> Dict[str, Any]:
        """
        Выполнение поискового запроса
        
        Args:
            query (str): Поисковый запрос
            top_k (int): Количество результатов (3-21)
            method (int): Метод поиска (1-полнотекстовый, 2-векторный, 3-гибридный)
        
        Returns:
            Dict[str, Any]: Результаты поиска
        """
        try:
            # Валидация параметров
            if not (3 <= top_k <= 21):
                raise ValueError("top_k должен быть от 3 до 21")
            if not (1 <= method <= 3):
                raise ValueError("method должен быть от 1 до 3")

            # Формирование запроса
            request_data = {
                "query": query,
                "top_k": top_k,
                "method": method
            }

            logger.info(f"Отправка запроса: {request_data}")
            
            # Выполнение запроса
            response = self.client.post(
                f"{self.base_url}/search",
                json=request_data
            )
            
            # Проверка статуса
            response.raise_for_status()
            
            # Получение результатов
            results = response.json()
            
            # Форматирование вывода
            formatted_results = self.format_results(results)
            return formatted_results

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', str(e))
            logger.error(f"Ошибка HTTP {e.response.status_code}: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            raise

    def format_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование результатов поиска"""
        formatted = {
            "результаты": [],
            "метрики": {}
        }

        # Форматирование результатов
        for item in results["results"]:
            formatted["результаты"].append({
                "id_фильма": item["movie_id"],
                "релевантность": round(item["score"], 3),
                "текст": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"],
                "источник": {
                    "fulltext": "полнотекстовый",
                    "vector": "векторный",
                    "hybrid": "гибридный"
                }.get(item["source"], item["source"])
            })

        # Форматирование метрик
        for key, value in results["metrics"].items():
            formatted_key = {
                "latency": "время_поиска",
                "max_score": "максимальная_релевантность",
                "total_results": "всего_найдено",
                "fulltext_max_score": "макс_полнотекстовый",
                "vector_max_score": "макс_векторный"
            }.get(key, key)
            
            formatted["метрики"][formatted_key] = round(value, 3) if isinstance(value, float) else value

        return formatted

    def save_results(self, results: Dict[str, Any], output_file: Path):
        """Сохранение результатов в файл"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Результаты сохранены в {output_file}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Клиент для поисковой системы')
    parser.add_argument('query', type=str, help='Поисковый запрос')
    parser.add_argument('--top-k', type=int, default=5, help='Количество результатов (3-21)')
    parser.add_argument('--method', type=int, default=1, 
                       help='Метод поиска: 1-полнотекстовый, 2-векторный, 3-гибридный')
    parser.add_argument('--output', type=Path, default=Path('results/search_results.json'),
                       help='Путь для сохранения результатов')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:8000',
                       help='URL поискового сервиса')

    args = parser.parse_args()

    try:
        with SearchClient(args.url) as client:
            results = client.search(
                query=args.query,
                top_k=args.top_k,
                method=args.method
            )
            
            # Вывод результатов в консоль
            print("\nРезультаты поиска:")
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
            # Сохранение результатов в файл
            client.save_results(results, args.output)

    except Exception as e:
        logger.error(f"Ошибка при выполнении поиска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()