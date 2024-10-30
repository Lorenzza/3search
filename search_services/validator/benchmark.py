"""
Валидатор поисковых методов:
- Полнотекстовый (fulltext)
- Векторный (vector)
- Гибридный (hybrid)
"""
import httpx
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import asyncio
from typing import List, Dict
import logging
import time
from datetime import datetime
from enum import IntEnum

class SearchMethod(IntEnum):
    FULLTEXT = 1
    VECTOR = 2
    HYBRID = 3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchValidator:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results_dir = Path("validation_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def run_search(self, query: str, top_k: int, method: SearchMethod) -> Dict:
        """Выполнение одного поискового запроса"""
        async with httpx.AsyncClient() as client:
            try:
                request_data = {
                    "query": query,
                    "top_k": top_k,
                    "method": int(method)
                }
                
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/search",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                actual_latency = time.time() - start_time
                
                result = response.json()
                results = result.get("results", [])
                metrics = result.get("metrics", {})
                
                similarities = [item.get("score", 0) for item in results]
                max_similarity = max(similarities) if similarities else 0
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                
                return {
                    "query": query,
                    "top_k": top_k,
                    "method": int(method),
                    "max_similarity": max_similarity,
                    "average_similarity": avg_similarity,
                    "total_results": len(results),
                    "reported_latency": metrics.get("latency", 0),
                    "actual_latency": actual_latency
                }
                
            except Exception as e:
                logger.error(f"Ошибка при запросе {query} (top_k={top_k}, method={method}): {str(e)}")
                return None

    async def validate_queries(self, queries: List[str]):
        """Валидация списка запросов"""
        results = []
        methods = [SearchMethod.FULLTEXT, SearchMethod.VECTOR, SearchMethod.HYBRID]
        method_names = {
            SearchMethod.FULLTEXT: "Полнотекстовый",
            SearchMethod.VECTOR: "Векторный",
            SearchMethod.HYBRID: "Гибридный"
        }
        
        total_requests = len(queries) * len(methods) * len(range(5, 21, 5))
        completed = 0
        
        for query in queries:
            for method in methods:
                for top_k in range(5, 21, 5):
                    result = await self.run_search(query, top_k, method)
                    if result:
                        result["method_name"] = method_names[method]
                        results.append(result)
                    
                    completed += 1
                    logger.info(f"Прогресс: {completed}/{total_requests} "
                              f"({(completed/total_requests*100):.1f}%)")

        if not results:
            raise Exception("Не удалось получить результаты валидации")

        df = pd.DataFrame(results)
        
        csv_path = self.results_dir / f"validation_results_{self.timestamp}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Результаты сохранены в {csv_path}")
        
        self.create_visualizations(df)
        return csv_path

    def create_visualizations(self, df: pd.DataFrame):
        """Создание визуализаций результатов"""
        try:
            # Используем стандартный стиль вместо seaborn
            plt.style.use('default')
            
            plots_dir = self.results_dir / f"plots_{self.timestamp}"
            plots_dir.mkdir(parents=True, exist_ok=True)

            # Настраиваем общие параметры для всех графиков
            plt.rcParams['figure.figsize'] = (12, 6)
            plt.rcParams['axes.grid'] = True
            plt.rcParams['axes.axisbelow'] = True

            # 1. Время выполнения
            try:
                plt.figure()
                sns.lineplot(data=df, x='top_k', y='actual_latency', hue='method_name', marker='o')
                plt.title('Время выполнения запроса', pad=20)
                plt.xlabel('Количество результатов')
                plt.ylabel('Время (секунды)')
                plt.tight_layout()
                plt.savefig(plots_dir / 'latency_by_top_k.png', dpi=300, bbox_inches='tight')
                plt.close()
            except Exception as e:
                logger.error(f"Ошибка при создании графика времени выполнения: {str(e)}")

            # 2. Максимальное сходство
            try:
                plt.figure()
                sns.boxplot(data=df, x='method_name', y='max_similarity')
                plt.title('Распределение максимального сходства по методам', pad=20)
                plt.xlabel('Метод поиска')
                plt.ylabel('Максимальное сходство')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(plots_dir / 'max_similarity_by_method.png', dpi=300, bbox_inches='tight')
                plt.close()
            except Exception as e:
                logger.error(f"Ошибка при создании графика максимального сходства: {str(e)}")

            # 3. Количество результатов
            try:
                plt.figure()
                sns.boxplot(data=df, x='method_name', y='total_results')
                plt.title('Распределение количества результатов по методам', pad=20)
                plt.xlabel('Метод поиска')
                plt.ylabel('Количество результатов')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(plots_dir / 'total_results_by_method.png', dpi=300, bbox_inches='tight')
                plt.close()
            except Exception as e:
                logger.error(f"Ошибка при создании графика количества результатов: {str(e)}")

            # 4. Тепловая карта корреляций
            try:
                plt.figure(figsize=(10, 8))
                correlation_matrix = df[['top_k', 'max_similarity', 'total_results', 'actual_latency']].corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
                plt.title('Корреляция метрик', pad=20)
                plt.tight_layout()
                plt.savefig(plots_dir / 'metrics_correlation.png', dpi=300, bbox_inches='tight')
                plt.close()
            except Exception as e:
                logger.error(f"Ошибка при создании тепловой карты корреляций: {str(e)}")

            # Статистический отчет
            try:
                stats = df.groupby('method_name').agg({
                    'actual_latency': ['mean', 'std', 'min', 'max'],
                    'max_similarity': ['mean', 'std', 'min', 'max'],
                    'total_results': ['mean', 'std', 'min', 'max']
                }).round(3)

                stats_path = plots_dir / 'statistics.txt'
                with open(stats_path, 'w', encoding='utf-8') as f:
                    f.write("Статистика по методам поиска:\n\n")
                    f.write(stats.to_string())
            except Exception as e:
                logger.error(f"Ошибка при создании статистического отчета: {str(e)}")

            logger.info(f"Визуализации сохранены в {plots_dir}")

        except Exception as e:
            logger.error(f"Ошибка при создании визуализаций: {str(e)}")