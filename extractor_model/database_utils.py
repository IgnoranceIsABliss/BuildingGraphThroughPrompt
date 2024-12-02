# extractor_model/database_utils.py

import psycopg2
import logging
import numpy as np

def create_metadata_tables(cursor):
    create_dashboards_table = """
    CREATE TABLE IF NOT EXISTS dashboards_metadata (
        dashboard_id INTEGER PRIMARY KEY,
        dashboard_title TEXT NOT NULL,
        embedding BYTEA
    );
    """
    create_charts_table = """
    CREATE TABLE IF NOT EXISTS charts_metadata (
        chart_id INTEGER PRIMARY KEY,
        chart_name TEXT NOT NULL,
        chart_description TEXT,
        embedding BYTEA,
        name_embedding BYTEA,
        dashboard_id INTEGER NULL,
        FOREIGN KEY (dashboard_id) REFERENCES dashboards_metadata(dashboard_id) ON DELETE SET NULL
    );
    """
    cursor.execute(create_dashboards_table)
    cursor.execute(create_charts_table)

def save_metadata_to_db(dashboards_data, charts_data, cursor, conn):
    # Сохранение дашбордов
    for dashboard in dashboards_data:
        try:
            insert_dashboard = """
            INSERT INTO dashboards_metadata (dashboard_id, dashboard_title, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (dashboard_id) DO UPDATE SET
            dashboard_title = EXCLUDED.dashboard_title,
            embedding = EXCLUDED.embedding;
            """
            cursor.execute(insert_dashboard, (
                dashboard['dashboard_id'],
                dashboard['dashboard_title'],
                psycopg2.Binary(dashboard['embedding'].tobytes()) if dashboard['embedding'] is not None else None
            ))
        except Exception as e:
            logging.error(f"Ошибка при сохранении дашборда {dashboard['dashboard_id']}: {e}")
            continue

    # Сохранение графиков
    for chart in charts_data:
        try:
            insert_chart = """
            INSERT INTO charts_metadata (chart_id, chart_name, chart_description, embedding, name_embedding, dashboard_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (chart_id) DO UPDATE SET
            chart_name = EXCLUDED.chart_name,
            chart_description = EXCLUDED.chart_description,
            embedding = EXCLUDED.embedding,
            name_embedding = EXCLUDED.name_embedding,
            dashboard_id = EXCLUDED.dashboard_id;
            """
            cursor.execute(insert_chart, (
                chart['chart_id'],
                chart['chart_name'],
                chart['chart_description'],
                psycopg2.Binary(chart['embedding'].tobytes()) if chart['embedding'] is not None else None,
                psycopg2.Binary(chart['name_embedding'].tobytes()) if chart.get('name_embedding') is not None else None,
                chart['dashboard_id']
            ))
        except Exception as e:
            logging.error(f"Ошибка при сохранении графика {chart['chart_id']}: {e}")
            continue

    conn.commit()

def load_metadata_from_db(cursor):
    dashboards_data = []
    charts_data = []

    # Загрузка дашбордов
    try:
        cursor.execute("SELECT dashboard_id, dashboard_title, embedding FROM dashboards_metadata;")
        dashboards = cursor.fetchall()
        for dashboard in dashboards:
            dashboard_id, dashboard_title, embedding_bytes = dashboard
            dashboard_embedding = np.frombuffer(embedding_bytes, dtype=np.float32) if embedding_bytes else None

            dashboards_data.append({
                'dashboard_id': dashboard_id,
                'dashboard_title': dashboard_title,
                'embedding': dashboard_embedding
            })
    except Exception as e:
        logging.error(f"Ошибка при загрузке дашбордов: {e}")

    # Загрузка графиков
    try:
        cursor.execute("SELECT chart_id, chart_name, chart_description, embedding, name_embedding, dashboard_id FROM charts_metadata;")
        charts = cursor.fetchall()
        for chart in charts:
            chart_id, chart_name, chart_description, embedding_bytes, name_embedding_bytes, dashboard_id = chart
            chart_embedding = np.frombuffer(embedding_bytes, dtype=np.float32) if embedding_bytes else None
            name_embedding = np.frombuffer(name_embedding_bytes, dtype=np.float32) if name_embedding_bytes else None
            chart_data = {
                'chart_id': chart_id,
                'chart_name': chart_name,
                'chart_description': chart_description,
                'embedding': chart_embedding,
                'name_embedding': name_embedding,
                'dashboard_id': dashboard_id
            }
            charts_data.append(chart_data)
    except Exception as e:
        logging.error(f"Ошибка при загрузке графиков: {e}")

    return dashboards_data, charts_data


def update_metadata_on_db(superset_url, superset_username, superset_password, db_connection_params):
    from .superset_client import SupersetClient
    from .database_utils import save_metadata_to_db
    from .dashboard_chart_utils import get_dashboards_and_charts

    try:
        # Подключаемся к базе данных и обновляем метаданные
        with psycopg2.connect(**db_connection_params) as conn:
            with conn.cursor() as cursor:
                # Инициализируем SupersetClient
                superset_client = SupersetClient(superset_url, superset_username, superset_password)
                superset_client.authenticate()

                # Получаем данные дашбордов и графиков
                dashboards_data, charts_data = get_dashboards_and_charts(superset_client)
                if not dashboards_data and not charts_data:
                    logging.error("Не удалось получить данные из Superset. Метаданные не будут обновлены.")
                    return

                # Сохраняем метаданные в базу данных
                save_metadata_to_db(dashboards_data, charts_data, cursor, conn)
                conn.commit()
                logging.info("Метаданные успешно обновлены.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении метаданных: {e}")