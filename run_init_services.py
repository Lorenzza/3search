import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_data():
    """Инициализация данных: создание индексов и векторизация"""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Создание векторного индекса
        logger.info("Создание векторного индекса...")
        vector_result = subprocess.run([
            sys.executable,
            "-m", "search_services.vector.indexer",
            "--path", "DATA/RAW/dataset"
        ], check=True, capture_output=True, text=True)
        
        if vector_result.returncode != 0:
            logger.error(f"Ошибка при создании векторного индекса: {vector_result.stderr}")
            return False
        
        logger.info(vector_result.stdout)

        # Инициализация Elasticsearch
        logger.info("Инициализация Elasticsearch...")
        es_result = subprocess.run([
            sys.executable,
            "-m", "prepare_data.init_elasticsearch"
        ], check=True, capture_output=True, text=True)
        
        if es_result.returncode != 0:
            logger.error(f"Ошибка при инициализации Elasticsearch: {es_result.stderr}")
            return False
        
        logger.info(es_result.stdout)
        
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении команды: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        if initialize_data():
            logger.info("Инициализация успешно завершена")
        else:
            logger.error("Не удалось создать индексы")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)