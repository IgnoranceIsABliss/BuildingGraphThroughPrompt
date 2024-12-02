# scheduler.py

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from extractor_model.database_utils import create_metadata_tables, update_metadata_on_db
from psycopg2 import connect
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Параметры подключения к базе данных из переменных окружения
db_connection_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Параметры подключения к Superset из переменных окружения
SUPERSET_URL = os.getenv('SUPERSET_URL')
SUPERSET_USERNAME = os.getenv('SUPERSET_USERNAME')
SUPERSET_PASSWORD = os.getenv('SUPERSET_PASSWORD')

scheduler = None  # Инициализируем переменную для планировщика

def init():
    logging.info("Инициализация приложения...")

    try:
        # Подключаемся к базе данных и создаем таблицы, если их нет
        with connect(**db_connection_params) as conn:
            with conn.cursor() as cursor:
                create_metadata_tables(cursor)
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        return

    # Обновляем метаданные при запуске
    update_metadata()

    # Запускаем планировщик
    start_scheduler()

def update_metadata():
    logging.info("Обновление метаданных...")
    update_metadata_on_db(
        superset_url=SUPERSET_URL,
        superset_username=SUPERSET_USERNAME,
        superset_password=SUPERSET_PASSWORD,
        db_connection_params=db_connection_params
    )



def start_scheduler():
    """
    Запуск планировщика для периодического обновления метаданных.
    """
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_metadata, 'interval', minutes=5)
    scheduler.start()
    logging.info("Планировщик запущен.")

def shutdown_scheduler():
    """
    Остановка планировщика.
    """
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logging.info("Планировщик остановлен.")
