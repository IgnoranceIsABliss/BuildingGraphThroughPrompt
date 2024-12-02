# main.py

import logging
import os
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from psycopg2 import connect
from extractor_model.entities_extractor import extract_entities
from scheduler import init, shutdown_scheduler

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Инициализация Flask приложения
app = Flask(__name__)
CORS(app)

@app.route('/open_dashboard', methods=['POST'])
def open_dashboard():
    """
    Эндпоинт для открытия дашборда по запросу пользователя.
    """
    try:
        data = request.get_json()
        user_query = data.get('query', '')

        if not user_query:
            return jsonify({"status": "error", "message": "Query is required"}), 400

        # Извлечение сущностей с помощью AI
        entities = extract_entities(
            text=user_query,
            db_connection_params=db_connection_params
        )

        # Проверка наличия ID дашборда
        dashboard_id = entities.get('dashboard_id')
        if not dashboard_id:
            return jsonify({"status": "error", "message": "No dashboard found for the query"}), 404

        # Формирование фильтров
        filters = entities.get('filters', [])
        filters_string = '&'.join(f.lstrip('?') for f in filters)  # Убираем '?' из каждого фильтра

        # Формирование конечного URL
        dashboard_url = f"{SUPERSET_URL.rstrip('/')}/superset/dashboard/{dashboard_id}/"
        if filters_string:
            dashboard_url += f"?{filters_string}"

        # Открытие URL в браузере
        webbrowser.open(dashboard_url)

        # Возврат результата пользователю
        return jsonify({"status": "success", "message": f"{dashboard_url}"}), 200

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"status": "error", "message": "An error occurred"}), 500

if __name__ == "__main__":
    try:
        # Вызываем функцию init(), которая инициализирует приложение и запускает планировщик
        init()
        # Запускаем Flask приложение
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # При завершении работы приложения останавливаем планировщик
        shutdown_scheduler()
        logging.info("Приложение завершено.")
