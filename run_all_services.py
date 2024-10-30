import subprocess
import signal
import sys
from pathlib import Path
import logging
import time  # Добавлен импорт time
import requests
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_indices():
    """Проверка наличия необходимых индексов"""
    data_dir = Path("data")
    required_files = ["vector_index.pkl", "documents.pkl", "index_info.json"]
    
    missing_files = []
    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        logger.error("Пожалуйста, запустите сначала run_init_services.py")
        return False
    
    return True

def run_services():
    """Запуск поисковых сервисов"""
    services = [
        {
            "name": "Fulltext Search Service",
            "module": "search_services.fulltext.service:app",
            "host": "127.0.0.1",
            "port": 8001
        },
        {
            "name": "Vector Search Service",
            "module": "search_services.vector.service:app",
            "host": "127.0.0.1",
            "port": 8002
        },
        {
            "name": "Search Router Service",
            "module": "search_services.router.service:app",
            "host": "127.0.0.1",
            "port": 8000
        },
        {
            "name": "Search Validator Service",
            "module": "search_services.validator.app:app",
            "host": "127.0.0.1",
            "port": 8003
        }
    ]
    
    processes = []
    try:
        # Запуск сервисов
        for service in services:
            cmd = [
                sys.executable, "-m", "uvicorn",
                service["module"],
                "--host", service["host"],
                "--port", str(service["port"]),
                "--reload"
            ]
            logger.info(f"Запуск {service['name']} на порту {service['port']}...")
            proc = subprocess.Popen(cmd)
            processes.append((service['name'], proc))

        logger.info("\nВсе сервисы запущены:")
        for service in services:
            logger.info(f"- {service['name']}: http://{service['host']}:{service['port']}")
        
        logger.info("\nДля запуска валидации используйте один из вариантов:")
        logger.info("""
1. Валидация с предустановленными запросами:
curl -X POST "http://127.0.0.1:8003/validate/default"

2. Валидация с пользовательскими запросами:
curl -X POST "http://127.0.0.1:8003/validate" \\
     -H "Content-Type: application/json" \\
     -d '{
           "queries": [
             "космические путешествия",
             "любовь и отношения",
             "детективная история"
           ]
         }'
        """)

        # Ожидание завершения работы
        while True:
            try:
                for name, proc in processes:
                    if proc.poll() is not None:
                        logger.error(f"Сервис {name} неожиданно завершил работу")
                        return
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\nПолучен сигнал завершения работы...")
                break

    except Exception as e:
        logger.error(f"Ошибка при запуске сервисов: {str(e)}")
    
    finally:
        # Корректное завершение всех процессов
        logger.info("\nЗавершение работы сервисов...")
        for name, proc in processes:
            try:
                logger.info(f"Остановка {name}...")
                proc.terminate()
                proc.wait(timeout=5)  # Ждем завершения процесса
            except subprocess.TimeoutExpired:
                logger.warning(f"Принудительное завершение {name}...")
                proc.kill()  # Принудительное завершение, если процесс не завершился
            except Exception as e:
                logger.error(f"Ошибка при остановке {name}: {str(e)}")

if __name__ == "__main__":
    try:
        if not check_indices():
            sys.exit(1)
        
        logger.info("Запуск поисковых сервисов...")
        run_services()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)