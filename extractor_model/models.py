# extractor_model/models.py

import logging
import spacy
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import pandas as pd
from fuzzywuzzy import fuzz, process
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Загрузка моделей и данных...")

# Загрузка моделей
nlp = spacy.load("ru_core_news_sm")

semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

classifier = pipeline("text-classification", model="extractor_model/model", tokenizer="extractor_model/model")

# Функции предобработки
def lemmatize_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

def normalize_text(text):
    replacements = [
        r"\b(акционерное общество|ао|общество с ограниченной ответственностью|ооо)\b",
        r"\b(публичное акционерное общество|пао)\b"
    ]
    for pattern in replacements:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()

def correct_spelling(text, vocabulary, threshold=80):
    corrected_words = []
    for word in text.split():
        match = process.extractOne(word, vocabulary, scorer=fuzz.token_set_ratio)
        if match and match[1] >= threshold:
            corrected_words.append(match[0])
        else:
            corrected_words.append(word)
    return " ".join(corrected_words)

# Загрузка и обработка данных
data = pd.read_csv("prepared_dataset.csv")

logging.info("Обработка данных...")
data['normalized_text'] = data['text'].apply(normalize_text)
data['lemmatized_text'] = data['normalized_text'].apply(lemmatize_text)
data['embedding'] = data['lemmatized_text'].apply(
    lambda x: semantic_model.encode(x, convert_to_tensor=True, show_progress_bar=False))

# Создание словаря для проверки орфографии
vocabulary = set(data['normalized_text'].str.split().sum())

logging.info("Модели и данные загружены.")
