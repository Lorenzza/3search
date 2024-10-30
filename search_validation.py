from typing import List, Dict
import numpy as np
from datetime import datetime
from tqdm import tqdm
import aiohttp
import asyncio

class SearchValidator:
    def __init__(self):
        self.test_queries = self._load_test_queries()
        self.search_methods = {
            'полнотекстовый': 'http://127.0.0.1:8001/search',
            'векторный': 'http://127.0.0.1:8002/search',
            'гибридный': None  # Будет вычисляться на основе результатов двух других методов
        }
        self.fulltext_weight = 0.5
        self.vector_weight = 0.5

    def _load_test_queries(self) -> List[Dict]:
        """Загрузка тестового набора запросов"""
        return [
            {"query_id": "q1", "text": "Фильм про зеленую милю"},
            {"query_id": "q2", "text": "Комедия про двух друзей"},
            {"query_id": "q3", "text": "Фильм про космос и путешествия"},
            {"query_id": "q4", "text": "Драма о семейных отношениях"},
            {"query_id": "q5", "text": "Фильм про супергероев"},
            {"query_id": "q6", "text": "Детектив с неожиданной развязкой"},
            {"query_id": "q7", "text": "Фильм про любовь"},
            {"query_id": "q8", "text": "Боевик с погонями"},
            {"query_id": "q9", "text": "Фильм про путешествия во времени"},
            {"query_id": "q10", "text": "Мультфильм для всей семьи"},
            {"query_id": "q11", "text": "Фильм про животных"},
            {"query_id": "q12", "text": "Фильм про зелёную милю"},
            {"query_id": "q13", "text": "Эффект Зеро отзыв"},
            {"query_id": "q14", "text": "Вилли Вонка"},
            {"query_id": "q15", "text": "Иван Васильевич меняет"}
        ]

    async def perform_search(self, session: aiohttp.ClientSession, url: str, 
                           query: str, k: int, is_vector: bool = False) -> Dict:
        """Выполняет поисковый запрос"""
        try:
            async with session.post(url, json={"query": query, "top_k": k}) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                for result in data['results']:
                    results.append({
                        'movie_id': result.get('movie_id', ''),
                        'review_id': result.get('review_id', '') or result.get('movie_id', ''),
                        'content': result.get('content', '') or result.get('snippet', ''),
                        'relevance_score': result.get('similarity', 0.0) if is_vector else result.get('relevance_score', 0.0)
                    })
                
                return {
                    'results': results,
                    'performance_metrics': {'latency': data.get('latency', 0.0)}
                }
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {str(e)}")
            return self._get_empty_response()

    def combine_results(self, fulltext_results: Dict, vector_results: Dict, k: int) -> Dict:
        """Объединяет результаты полнотекстового и векторного поиска"""
        combined_results = {}
        
        # Объединение результатов
        for result in fulltext_results['results']:
            combined_results[result['review_id']] = {
                **result,
                'relevance_score': result['relevance_score'] * self.fulltext_weight
            }

        for result in vector_results['results']:
            if result['review_id'] in combined_results:
                combined_results[result['review_id']]['relevance_score'] += \
                    result['relevance_score'] * self.vector_weight
            else:
                combined_results[result['review_id']] = {
                    **result,
                    'relevance_score': result['relevance_score'] * self.vector_weight
                }

        # Сортировка и ограничение количества результатов
        sorted_results = sorted(
            combined_results.values(), 
            key=lambda x: x['relevance_score'], 
            reverse=True
        )[:k]

        return {
            'results': sorted_results,
            'performance_metrics': {
                'latency': max(
                    fulltext_results['performance_metrics']['latency'],
                    vector_results['performance_metrics']['latency']
                )
            }
        }

    async def run_validation(self) -> Dict:
        """Запуск процесса валидации"""
        results = {method: [] for method in self.search_methods}
        metrics = {method: {} for method in self.search_methods}
        
        async with aiohttp.ClientSession() as session:
            for query in tqdm(self.test_queries):
                try:
                    # Получаем результаты полнотекстового и векторного поиска
                    fulltext_results = await self.perform_search(
                        session, 
                        self.search_methods['полнотекстовый'],
                        query['text'], 
                        k=10
                    )
                    
                    vector_results = await self.perform_search(
                        session, 
                        self.search_methods['векторный'],
                        query['text'], 
                        k=10,
                        is_vector=True
                    )
                    
                    # Сохраняем результаты
                    results['полнотекстовый'].append({
                        'query_id': query['query_id'],
                        'query_text': query['text'],
                        'response': fulltext_results
                    })
                    
                    results['векторный'].append({
                        'query_id': query['query_id'],
                        'query_text': query['text'],
                        'response': vector_results
                    })
                    
                    # Получаем гибридные результаты
                    hybrid_results = self.combine_results(fulltext_results, vector_results, k=10)
                    results['гибридный'].append({
                        'query_id': query['query_id'],
                        'query_text': query['text'],
                        'response': hybrid_results
                    })
                    
                    # Расчет метрик для каждого метода
                    for method in self.search_methods:
                        query_metrics = self._calculate_query_metrics(
                            results[method][-1]['response']
                        )
                        self._aggregate_metrics(metrics[method], query_metrics)
                        
                except Exception as e:
                    print(f"Ошибка при обработке запроса {query['query_id']}: {str(e)}")
        
        return self._generate_validation_report(results, metrics)

    def _calculate_query_metrics(self, response: Dict) -> Dict:
        """Расчет метрик для отдельного запроса"""
        results = response['results']
        scores = [r['relevance_score'] for r in results]
        
        return {
            'performance_metrics': response['performance_metrics'],
            'ranking_metrics': self._calculate_ranking_metrics(results),
            'confidence_metrics': self._calculate_confidence_metrics(scores),
            'result_diversity': self._calculate_result_diversity(results)
        }
    
    def _calculate_result_diversity(self, results: List[Dict]) -> float:
        """Расчет разнообразия результатов"""
        # Можно использовать, например, среднее попарное расстояние между оценками
        scores = [r["relevance_score"] for r in results]
        if len(scores) < 2:
            return 0.0
        
        pairs = [(scores[i], scores[j]) 
                for i in range(len(scores)) 
                for j in range(i+1, len(scores))]
        
        distances = [abs(a - b) for a, b in pairs]
        return float(np.mean(distances))

    def _calculate_score_distribution(self, results: List[Dict]) -> Dict:
        """Анализ распределения оценок"""
        scores = [r["relevance_score"] for r in results]
        return {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "median": float(np.median(scores))
        }

    def _aggregate_metrics(self, aggregated_metrics: Dict, query_metrics: Dict):
        """Агрегация метрик по всем запросам"""
        for metric_type, metrics in query_metrics.items():
            if metric_type not in aggregated_metrics:
                aggregated_metrics[metric_type] = {}
            
            if isinstance(metrics, dict):
                for metric_name, value in metrics.items():
                    if metric_name not in aggregated_metrics[metric_type]:
                        aggregated_metrics[metric_type][metric_name] = []
                    aggregated_metrics[metric_type][metric_name].append(value)
            else:
                if "values" not in aggregated_metrics[metric_type]:
                    aggregated_metrics[metric_type]["values"] = []
                aggregated_metrics[metric_type]["values"].append(metrics)

    def _generate_validation_report(self, results: Dict, metrics: Dict) -> Dict:
        """Генерация итогового отчета"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(metrics),
            "detailed_metrics": metrics,
            "visualizations": self._generate_visualizations(results, metrics),
            "method_comparison": self._compare_methods(results, metrics)
        }
        return report

    def _generate_summary(self, metrics: Dict) -> Dict:
        """Генерация сводной информации по метрикам"""
        summary = {}
        for method in self.search_methods:
            method_metrics = metrics[method]
            
            # Расчет средних значений метрик
            summary[method] = {
                "average_latency": np.mean(method_metrics["performance_metrics"]["latency"]),
                "average_confidence": np.mean(method_metrics["confidence_metrics"]["mean_relevance"]),
                "result_diversity": np.mean(method_metrics["result_diversity"]["values"]),
                "score_distribution": {
                    metric: np.mean(values) 
                    for metric, values in method_metrics["score_distribution"].items()
                }
            }
        return summary

    def _compare_methods(self, results: Dict, metrics: Dict) -> Dict:
        """Сравнительный анализ методов"""
        comparison = {
            "performance_ranking": self._rank_methods_by_metric(
                metrics, "performance_metrics", "latency", reverse=True
            ),
            "confidence_ranking": self._rank_methods_by_metric(
                metrics, "confidence_metrics", "mean_relevance"
            ),
            "diversity_ranking": self._rank_methods_by_metric(
                metrics, "result_diversity", "values"
            ),
            "stability_analysis": self._analyze_stability(metrics)
        }
        return comparison

    def _rank_methods_by_metric(self, metrics: Dict, metric_type: str, 
                              metric_name: str, reverse: bool = False) -> List[Dict]:
        """Ранжирование методов по заданной метрике"""
        method_scores = []
        for method in self.search_methods:
            if metric_name == "values":
                score = np.mean(metrics[method][metric_type]["values"])
            else:
                score = np.mean(metrics[method][metric_type][metric_name])
            method_scores.append({"method": method, "score": score})
        
        return sorted(method_scores, key=lambda x: x["score"], reverse=reverse)

    def _analyze_stability(self, metrics: Dict) -> Dict:
        """Анализ стабильности методов"""
        stability = {}
        for method in self.search_methods:
            stability[method] = {
                "latency_std": np.std(metrics[method]["performance_metrics"]["latency"]),
                "confidence_std": np.std(metrics[method]["confidence_metrics"]["mean_relevance"]),
                "score_stability": np.mean([
                    np.std(metrics[method]["score_distribution"][metric])
                    for metric in ["mean", "median"]
                ])
            }
        return stability

    def _generate_visualizations(self, results: Dict, metrics: Dict) -> Dict:
        """Генерация визуализаций"""
        visualizations = {}
        
        # График сравнения методов
        self._plot_methods_comparison(metrics)
        visualizations["methods_comparison"] = "methods_comparison.png"
        
        # График времени отклика
        self._plot_latency_comparison(metrics)
        visualizations["latency_comparison"] = "latency_comparison.png"
        
        # График распределения оценок
        self._plot_score_distribution(results)
        visualizations["score_distribution"] = "score_distribution.png"
        
        return visualizations

    def _plot_methods_comparison(self, metrics: Dict):
        """График сравнения методов"""
        plt.figure(figsize=(12, 6))
        
        metrics_to_plot = ["mean_relevance", "result_diversity"]
        x = np.arange(len(self.search_methods))
        width = 0.35
        
        for i, metric in enumerate(metrics_to_plot):
            values = []
            for method in self.search_methods:
                if metric == "result_diversity":
                    values.append(np.mean(metrics[method]["result_diversity"]["values"]))
                else:
                    values.append(np.mean(metrics[method]["confidence_metrics"][metric]))
            
            plt.bar(x + i*width, values, width, label=metric)
        
        plt.xlabel('Методы поиска')
        plt.ylabel('Значение метрики')
        plt.title('Сравнение методов поиска')
        plt.xticks(x + width/2, self.search_methods)
        plt.legend()
        
        plt.savefig('methods_comparison.png')
        plt.close()

    def _plot_latency_comparison(self, metrics: Dict):
        """График сравнения времени отклика"""
        plt.figure(figsize=(10, 6))
        
        data = []
        labels = []
        for method in self.search_methods:
            latencies = metrics[method]["performance_metrics"]["latency"]
            data.append(latencies)
            labels.extend([method] * len(latencies))
        
        plt.boxplot(data, labels=self.search_methods)
        plt.ylabel('Время отклика (сек)')
        plt.title('Сравнение времени отклика методов')
        
        plt.savefig('latency_comparison.png')
        plt.close()

    def _plot_score_distribution(self, results: Dict):
        """График распределения оценок релевантности"""
        plt.figure(figsize=(12, 6))
        
        for method in self.search_methods:
            scores = []
            for result in results[method]:
                scores.extend([r["relevance_score"] for r in result["response"]["results"]])
            
            sns.kdeplot(data=scores, label=method)
        
        plt.xlabel('Оценка релевантности')
        plt.ylabel('Плотность')
        plt.title('Распределение оценок релевантности')
        plt.legend()
        
        plt.savefig('score_distribution.png')
        plt.close()