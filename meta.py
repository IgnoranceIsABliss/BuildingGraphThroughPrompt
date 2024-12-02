import requests

# Укажите URL вашего экземпляра Superset
url = 'http://localhost:8088'

# Укажите свои учетные данные
username = 'xx'
password = 'xx'

# Аутентификация и получение токена доступа
auth_response = requests.post(f'{url}/api/v1/security/login', json={
    'username': username,
    'password': password,
    'provider': 'db'
})

if auth_response.status_code == 200:
    auth_token = auth_response.json()['access_token']
    print("Аутентификация прошла успешно.")
else:
    print(f"Ошибка аутентификации: {auth_response.status_code} - {auth_response.text}")
    exit()

# Заголовки для последующих запросов
headers = {
    'Authorization': f'Bearer {auth_token}'
}

# Получение списка дашбордов
dashboards_response = requests.get(f'{url}/api/v1/dashboard/', headers=headers)

if dashboards_response.status_code == 200:
    dashboards = dashboards_response.json()
    print("Список дашбордов:")
    for dashboard in dashboards['result']:
        print(f"- {dashboard['dashboard_title']} (ID: {dashboard['id']})")
        # Получение графиков для каждого дашборда
        charts_response = requests.get(f"{url}/api/v1/dashboard/{dashboard['id']}/charts", headers=headers)
        if charts_response.status_code == 200:
            charts = charts_response.json()['result']
            print("  Графики:")
            for chart in charts:
                print(f"    - {chart['slice_name']} (ID: {chart['id']})")
        else:
            print(f"  Ошибка при получении графиков: {charts_response.status_code} - {charts_response.text}")
else:
    print(f"Ошибка при получении дашбордов: {dashboards_response.status_code} - {dashboards_response.text}")
