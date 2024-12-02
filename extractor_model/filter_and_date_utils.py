import logging
import re
import calendar
from datetime import date, datetime
import dateparser
from fuzzywuzzy import fuzz, process
from sentence_transformers import util
from extractor_model.models import semantic_model, data, classifier, vocabulary, lemmatize_text, normalize_text, correct_spelling

# Функция для извлечения фильтров с помощью классификатора
def find_filters_with_classifier(text):
    filters = []
    label_map = {0: "client", 1: "service", 2: "management", 3: "status", 4: "workgroup", 5: "type"}

    normalized_query = normalize_text(text)
    corrected_query = correct_spelling(normalized_query, vocabulary)
    logging.info(f"Corrected Query: {corrected_query}")

    lemmatized_query = lemmatize_text(corrected_query)

    text_embedding = semantic_model.encode(lemmatized_query, convert_to_tensor=True, show_progress_bar=False)

    for _, row in data.iterrows():
        lemmatized_row_text = row['lemmatized_text']

        similarity = util.cos_sim(text_embedding, row['embedding']).item()

        if similarity >= 0.5:
            fuzzy_score = fuzz.token_set_ratio(lemmatized_row_text.lower(), lemmatized_query.lower())
            if fuzzy_score >= 90:
                prediction = classifier(row["text"])[0]
                predicted_label = int(prediction["label"].replace("LABEL_", ""))
                filters.append(f"?{label_map[predicted_label]}={row['text']}")

    return filters

# Функция для извлечения даты из текста
def extract_date(text):
    # Функция для исправления названий месяцев
    def correct_month(input_month):
        month_mapping = {
            "январь": "01", "января": "01",
            "февраль": "02", "февраля": "02",
            "март": "03", "марта": "03",
            "апрель": "04", "апреля": "04",
            "май": "05", "мая": "05",
            "июнь": "06", "июня": "06",
            "июль": "07", "июля": "07",
            "август": "08", "августа": "08",
            "сентябрь": "09", "сентября": "09",
            "октябрь": "10", "октября": "10",
            "ноябрь": "11", "ноября": "11",
            "декабрь": "12", "декабря": "12"
        }
        corrected_month = process.extractOne(input_month.lower(), month_mapping.keys())
        return month_mapping.get(corrected_month[0]) if corrected_month else None
    
    regex_patterns = {
        # Интервалы между конкретными датами
        "date_interval": r'\bс\s+(\d{1,2})\s+([а-яА-Я]+)\s+(\d{2,4})(?:\s+года?)?\s+по\s+(\d{1,2})\s+([а-яА-Я]+)\s+(\d{2,4})(?:\s+года?)?\b',
        # Интервалы между месяцами без указания года
        "month_interval": r'\bс\s+([а-яА-Я]+)\s+по\s+([а-яА-Я]+)\b',
        "year": r'\b(?:за|в|на)\s+(\d{2,4})\s+год[ауе]?\b',
        "interval": r'\bс\s+([а-яА-Я]+)\s+(\d{2,4})\s+по\s+([а-яА-Я]+)\s+(\d{2,4})\b',
        "single_date": [
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b',
            r'\b(\d{1,2})\s+([а-яА-Я]+)\s+(\d{2,4})(?:\s+года?)?\b',
            r'\b(\d{1,2})\s+([а-яА-Я]+)(?:\s+года?)?\b'
        ],
        "month_year": r'\b([а-яА-Я]+)\s+(\d{2,4})(?:\s+года?)?\b'
    }

    # Интервал между конкретными датами
    date_interval_match = re.search(regex_patterns["date_interval"], text, re.IGNORECASE)
    if date_interval_match:
        start_day, start_month_name, start_year, end_day, end_month_name, end_year = date_interval_match.groups()
        start_month = correct_month(start_month_name)
        end_month = correct_month(end_month_name)
        if start_month and end_month:
            start_year = f"20{start_year}" if len(start_year) == 2 else start_year
            end_year = f"20{end_year}" if len(end_year) == 2 else end_year
            start_date_obj = date(int(start_year), int(start_month), int(start_day))
            end_date_obj = date(int(end_year), int(end_month), int(end_day))
            return f"{start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}"

    # Интервал между месяцами без указания года
    month_interval_match = re.search(regex_patterns["month_interval"], text, re.IGNORECASE)
    if month_interval_match:
        start_month_name, end_month_name = month_interval_match.groups()
        start_month = correct_month(start_month_name)
        end_month = correct_month(end_month_name)
        if start_month and end_month:
            current_year = datetime.now().year
            # Если начальный месяц больше конечного, считаем, что интервал переходит через год
            if int(start_month) > int(end_month):
                start_year = current_year - 1
                end_year = current_year
            else:
                start_year = end_year = current_year
            start_date_obj = date(start_year, int(start_month), 1)
            last_day = calendar.monthrange(end_year, int(end_month))[1]
            end_date_obj = date(end_year, int(end_month), last_day)
            return f"{start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}"

    # Интервал дат (месяцы и годы)
    interval_match = re.search(regex_patterns["interval"], text, re.IGNORECASE)
    if interval_match:
        start_month_name, start_year, end_month_name, end_year = interval_match.groups()
        start_month = correct_month(start_month_name)
        end_month = correct_month(end_month_name)
        if start_month and end_month:
            start_year = f"20{start_year}" if len(start_year) == 2 else start_year
            end_year = f"20{end_year}" if len(end_year) == 2 else end_year
            start_date_obj = date(int(start_year), int(start_month), 1)
            last_day = calendar.monthrange(int(end_year), int(end_month))[1]
            end_date_obj = date(int(end_year), int(end_month), last_day)
            return f"{start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}"

    # Год
    year_match = re.search(regex_patterns["year"], text, re.IGNORECASE)
    if year_match:
        year = year_match.group(1)
        year = f"20{year}" if len(year) == 2 else year
        start_date_obj = date(int(year), 1, 1)
        end_date_obj = date(int(year), 12, 31)
        return f"{start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}"

    # Одиночные даты
    for pattern in regex_patterns["single_date"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                day, month_or_name, year = groups
                if month_or_name.isdigit():
                    month = month_or_name.zfill(2)
                else:
                    month = correct_month(month_or_name)
                if month:
                    year = f"20{year}" if len(year) == 2 else year
                    return f"{year}-{month}-{day.zfill(2)}"
            elif len(groups) == 2:
                day, month_or_name = groups
                if month_or_name.isdigit():
                    month = month_or_name.zfill(2)
                else:
                    month = correct_month(month_or_name)
                if month:
                    year = datetime.now().year
                    return f"{year}-{month}-{day.zfill(2)}"

    # Месяц и год
    month_year_match = re.search(regex_patterns["month_year"], text, re.IGNORECASE)
    if month_year_match:
        month_name, year = month_year_match.groups()
        month = correct_month(month_name)
        if month:
            year = f"20{year}" if len(year) == 2 else year
            start_date_obj = date(int(year), int(month), 1)
            last_day = calendar.monthrange(int(year), int(month))[1]
            end_date_obj = date(int(year), int(month), last_day)
            return f"{start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}"

    # Попытка распарсить дату с помощью dateparser
    date_obj = dateparser.parse(text, languages=['ru'])
    if date_obj:
        return date_obj.strftime("%Y-%m-%d")

    return None
