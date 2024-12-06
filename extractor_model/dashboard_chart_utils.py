# extractor_model/dashboard_chart_utils.py

import logging
from sentence_transformers import util
from .models import semantic_model
from fuzzywuzzy import fuzz

def get_dashboards_and_charts(superset_client):
    dashboards_data = []
    charts_data = []
    processed_chart_ids = set()

    # Внутренняя функция для безопасного преобразования в строку
    def safe_str(s):
        return str(s) if s else ''

    # Получение всех дашбордов
    dashboards_response = superset_client.get('/api/v1/dashboard/')
    if dashboards_response.status_code != 200:
        logging.error(f"Ошибка при получении дашбордов: {dashboards_response.status_code} - {dashboards_response.text}")
        return dashboards_data, charts_data

    dashboards = dashboards_response.json().get('result', [])

    if not dashboards:
        logging.warning("Список дашбордов пуст.")
        return dashboards_data, charts_data

    # Обработка дашбордов и связанных с ними графиков
    for dashboard in dashboards:
        dashboard_id = dashboard.get('id')
        dashboard_title = safe_str(dashboard.get('dashboard_title')).strip()

        if not dashboard_id or not dashboard_title:
            logging.warning(f"Пропущен дашборд с неполными данными: {dashboard}")
            continue

        try:
            # Создаем эмбеддинг только из названия дашборда
            dashboard_embedding = semantic_model.encode(dashboard_title, show_progress_bar=False)
        except Exception as e:
            logging.error(f"Ошибка при создании эмбеддинга для дашборда {dashboard_id}: {e}")
            dashboard_embedding = None

        dashboards_data.append({
            'dashboard_id': dashboard_id,
            'dashboard_title': dashboard_title,
            'embedding': dashboard_embedding
        })

        # Получаем графики, связанные с данным дашбордом
        charts_response = superset_client.get(f"/api/v1/dashboard/{dashboard_id}/charts")
        if charts_response.status_code != 200:
            logging.error(f"Ошибка при получении графиков для дашборда {dashboard_id}: {charts_response.status_code} - {charts_response.text}")
            continue

        charts = charts_response.json().get('result', [])
        for chart in charts:
            chart_id = chart.get('id')
            chart_name = safe_str(chart.get('slice_name')).strip()
            chart_description = safe_str(chart.get('description')).strip()

            if not chart_id or not chart_name:
                logging.warning(f"Пропущен график с неполными данными: {chart}")
                continue

            try:
                # Создаем эмбеддинг из описания графика, если оно есть
                chart_embedding = semantic_model.encode(chart_description, show_progress_bar=False) if chart_description else None
                # Создаем эмбеддинг из названия графика
                chart_name_embedding = semantic_model.encode(chart_name, show_progress_bar=False)
            except Exception as e:
                logging.error(f"Ошибка при создании эмбеддинга для графика {chart_id}: {e}")
                chart_embedding = None
                chart_name_embedding = None

            charts_data.append({
                'chart_id': chart_id,
                'chart_name': chart_name,
                'chart_description': chart_description,
                'embedding': chart_embedding,
                'name_embedding': chart_name_embedding,
                'dashboard_id': dashboard_id
            })
            processed_chart_ids.add(chart_id)

    # Получение всех графиков (не связанных с дашбордами)
    charts_response = superset_client.get('/api/v1/chart/')
    if charts_response.status_code != 200:
        logging.error(f"Ошибка при получении графиков: {charts_response.status_code} - {charts_response.text}")
        return dashboards_data, charts_data

    all_charts = charts_response.json().get('result', [])

    for chart in all_charts:
        chart_id = chart.get('id')
        chart_name = safe_str(chart.get('slice_name')).strip()
        chart_description = safe_str(chart.get('description')).strip()

        if not chart_id or not chart_name:
            logging.warning(f"Пропущен график с неполными данными: {chart}")
            continue

        if chart_id in processed_chart_ids:
            continue  # Уже обработан, связан с дашбордом

        try:
            # Создаем эмбеддинг из описания графика, если оно есть
            chart_embedding = semantic_model.encode(chart_description, show_progress_bar=False) if chart_description else None
            # Создаем эмбеддинг из названия графика
            chart_name_embedding = semantic_model.encode(chart_name, show_progress_bar=False)
        except Exception as e:
            logging.error(f"Ошибка при создании эмбеддинга для графика {chart_id}: {e}")
            chart_embedding = None
            chart_name_embedding = None

        charts_data.append({
            'chart_id': chart_id,
            'chart_name': chart_name,
            'chart_description': chart_description,
            'embedding': chart_embedding,
            'name_embedding': chart_name_embedding,
            'dashboard_id': None
        })

    return dashboards_data, charts_data

def find_dashboard_and_chart(query, dashboards_data, charts_data):
    max_similarity_dashboard = 0.65  # Порог для дашбордов
    max_similarity_chart = 0.55      # Порог для графиков
    dashboard_keywords = ["дашборд", "dashboard", "панель"]
    fuzzy_threshold = 85

    try:
        query_lower = query.lower()
        query_words = query_lower.split()

        matched_dashboard = None
        matched_chart = None

        # Вспомогательная функция для поиска лучшего совпадения по эмбеддингу
        def find_best_match(data, query_embedding, max_similarity, embedding_fields=['embedding']):
            best_match = None
            best_similarity = -1
            for item in data:
                for field in embedding_fields:
                    if field in item and item[field] is not None:
                        similarity = util.cos_sim(query_embedding, item[field]).item()
                        if similarity > best_similarity and similarity >= max_similarity:
                            best_similarity = similarity
                            best_match = item
            return best_match, best_similarity

        # Функция для поиска дашборда по ключевым словам
        def search_dashboard_by_keywords(query_words, dashboard_keywords, dashboards_data, fuzzy_threshold):
            for i, word in enumerate(query_words):
                for keyword in dashboard_keywords:
                    ratio = fuzz.ratio(word, keyword)
                    # Если совпадение с ключевым словом достаточно высокое
                    if ratio >= fuzzy_threshold:
                        # Предполагаем, что название дашборда следует в ближайших словах
                        potential_name_words = query_words[i+1:i+11]
                        potential_name = " ".join(potential_name_words).strip()
                        if potential_name:
                            local_query_embedding = semantic_model.encode(potential_name, convert_to_tensor=True, show_progress_bar=False)
                            matched_db, sim = find_best_match(dashboards_data, local_query_embedding, max_similarity_dashboard)
                            if matched_db:
                                return matched_db, sim
            return None, -1

        # Создаём эмбеддинг для полного запроса
        query_embedding = semantic_model.encode(query, convert_to_tensor=True, show_progress_bar=False)

        # 1. Пытаемся найти дашборд по ключевым словам
        matched_dashboard, dashboard_similarity = search_dashboard_by_keywords(query_words, dashboard_keywords, dashboards_data, fuzzy_threshold)

        # 2. Если дашборд не найден по ключевым словам, ищем по всему запросу
        if not matched_dashboard:
            matched_dashboard, dashboard_similarity = find_best_match(dashboards_data, query_embedding, max_similarity_dashboard)

        # 3. Если дашборд найден, ищем график внутри него
        if matched_dashboard:
            logging.info(f"Найден дашборд: {matched_dashboard.get('dashboard_title', 'Без названия')} (схожесть: {dashboard_similarity:.2f})")
            relevant_charts = [chart for chart in charts_data if chart.get('dashboard_id') == matched_dashboard.get('dashboard_id')]
            matched_chart, chart_similarity = find_best_match(relevant_charts, query_embedding, max_similarity_chart, embedding_fields=['embedding', 'name_embedding'])
            if matched_chart:
                logging.info(f"Найден график на указанном дашборде: {matched_chart.get('chart_name', 'Без названия')} (схожесть: {chart_similarity:.2f})")
            else:
                logging.info("На указанном дашборде не найдено подходящих графиков.")
        else:
            # 4. Если дашборд не найден, пытаемся найти график по всему запросу
            matched_chart, chart_similarity = find_best_match(charts_data, query_embedding, max_similarity_chart, embedding_fields=['embedding', 'name_embedding'])
            if matched_chart:
                logging.info(f"Найден график: {matched_chart.get('chart_name', 'Без названия')} (схожесть: {chart_similarity:.2f})")
                # Пытаемся определить дашборд, к которому относится этот график
                dashboard_id = matched_chart.get('dashboard_id')
                if dashboard_id:
                    dashboard_of_chart = next((d for d in dashboards_data if d.get('dashboard_id') == dashboard_id), None)
                    if dashboard_of_chart:
                        matched_dashboard = dashboard_of_chart
                        logging.info(f"Связанный дашборд: {matched_dashboard.get('dashboard_title', 'Без названия')}")
                    else:
                        logging.info("Связанный дашборд не найден.")
                else:
                    logging.info("У графика отсутствует dashboard_id.")
            else:
                logging.info("Не найден соответствующий дашборд или график по запросу.")

        return matched_dashboard, matched_chart

    except Exception as e:
        logging.error(f"Ошибка при поиске дашборда и графика: {e}")
        return None, None

