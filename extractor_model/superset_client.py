# extractor_model/superset_client.py

import requests
from datetime import datetime, timedelta
import logging

class SupersetClient:
    def __init__(self, superset_url, username, password):
        self.superset_url = superset_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = None  # Время истечения токена
        self.headers = None

    def authenticate(self):
        auth_response = requests.post(f'{self.superset_url}/api/v1/security/login', json={
            'username': self.username,
            'password': self.password,
            'provider': 'db'
        })

        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            self.token = auth_data['access_token']
            # Предполагаем, что токен действителен 1 час
            self.token_expiry = datetime.now() + timedelta(hours=1)
            self.headers = {
                'Authorization': f'Bearer {self.token}'
            }
            logging.info("Аутентификация успешна.")
        else:
            raise Exception(f"Ошибка аутентификации: {auth_response.status_code} - {auth_response.text}")

    def ensure_authenticated(self):
        if not self.token or datetime.now() >= self.token_expiry:
            logging.info("Токен отсутствует или истек. Повторная аутентификация.")
            self.authenticate()

    def get(self, endpoint):
        self.ensure_authenticated()
        response = requests.get(f'{self.superset_url}{endpoint}', headers=self.headers)
        if response.status_code == 401:
            logging.info("Недействительный токен. Повторная аутентификация.")
            self.authenticate()
            response = requests.get(f'{self.superset_url}{endpoint}', headers=self.headers)
        return response
