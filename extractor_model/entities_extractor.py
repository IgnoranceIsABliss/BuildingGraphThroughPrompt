# extractor_model/entities_extractor.py

import logging
from .filter_and_date_utils import find_filters_with_classifier, extract_date
from .dashboard_chart_utils import find_dashboard_and_chart
from .database_utils import load_metadata_from_db
import psycopg2

def extract_entities(text, db_connection_params):
    logging.info("Начало извлечения сущностей...")
    try:
        # Подключаемся к базе данных и загружаем метаданные
        with psycopg2.connect(**db_connection_params) as conn:
            with conn.cursor() as cursor:
                dashboards_data, charts_data = load_metadata_from_db(cursor)

        # Извлечение дашборда и графика
        dashboard, chart = find_dashboard_and_chart(text, dashboards_data, charts_data)

        # Извлечение даты
        extracted_date = extract_date(text)

        # Извлечение фильтров с помощью классификатора
        filters = find_filters_with_classifier(text)

        # Добавление даты в фильтры
        if extracted_date:
            if ' - ' in extracted_date:
                start_date, end_date = extracted_date.split(' - ')
                filters.append(f"?start_date={start_date}")
                filters.append(f"?end_date={end_date}")
            else:
                filters.append(f"?date={extracted_date}")

        entities = {
            "dashboard_id": dashboard['dashboard_id'] if dashboard else None,
            "chart_id": chart['chart_id'] if chart else None,
            "filters": filters
        }

    except Exception as e:
        logging.error(f"Ошибка при извлечении сущностей: {e}")
        entities = {
            "dashboard_id": None,
            "chart_id": None,
            "filters": []
        }

    logging.info("Извлечение сущностей завершено.")
    return entities


