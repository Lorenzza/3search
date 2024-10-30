import asyncio
from search_validation import SearchValidator
import json

async def main():
    # Инициализация валидатора
    validator = SearchValidator()
    
    # Запуск валидации (без передачи search_client)
    validation_report = await validator.run_validation()
    
    # Сохранение отчета
    with open('validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, ensure_ascii=False, indent=2)
    
    # Вывод краткого отчета
    print("\nСравнительный анализ методов поиска:")
    print("-" * 80)
    
    for method in validator.search_methods:
        print(f"\nМетод: {method}")
        if method in validation_report.get('summary', {}):
            metrics = validation_report['summary'][method]
            print(f"Среднее время отклика: {metrics.get('average_latency', 0):.4f} сек")
            print(f"Средняя релевантность: {metrics.get('average_relevance', 0):.4f}")
            print(f"Разнообразие результатов: {metrics.get('average_diversity', 0):.4f}")
        else:
            print("Метрики недоступны")

if __name__ == "__main__":
    asyncio.run(main())