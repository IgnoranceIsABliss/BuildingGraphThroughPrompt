Рекомендую сразу создать 3 терминала и разрешить выполнение локальных скриптов командой, 
которую нужно ввести в PowerShell от имени администратора:

Set-ExecutionPolicy RemoteSigned




В этом проекте должны быть:

создайте файл .env в корневой папке проекта WEB-APP если его нет и впишите туда данные для подключения к базе данных и Superset:

SUPERSET_URL=http://localhost:8088/
SUPERSET_USERNAME=admin
SUPERSET_PASSWORD=admin

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=keymaster
DB_HOST=192.168.0.11
DB_PORT=5432

только свои параметры

1) Первый терминал рекомендую создать для запуска apache superset

Откройте файл superset_config.py и впишите там:

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

запустите Apache Superset командой:

docker compose up

в самом apache superset сделать источником данных для каждого графика в дашборде скрипт:

SELECT * 
FROM requests
WHERE 1 = 1
{% for column in ['id', 'requestnumber', 'date', 'status', 'type', 'workgroup', 'management', 'service', 'servicecomponent', 'client', 'year', 'overdue', 'vip', 'hashtag', 'completiondate', 'standardclosuredate', 'month', 'monthname', 'statuscategory', 'datetime', 'closurecode', 'closedbytemplate', 'massrequest', 'dataloaddate', 'lastdataloaddate', 'sla_count', 'sla_duration', 'daydifference', 'autoprocess', 'lastorderclosed'] %}
    {% if url_param(column) %}
        {% set param_value = url_param(column).strip() %}
        {% if column in ['year', 'month', 'sla_count', 'sla_duration', 'daydifference'] %}
            AND {{ column }} IN ({{ param_value.split(',') | join(', ') }})
        {% else %}
            AND {{ column }} IN (
                {{ "'" + param_value.replace(",", "','").strip() + "'" }}
            )
        {% endif %}
    {% endif %}
{% endfor %}

Чтобы задать каждому графику новый источник данных, нужно:
    1) Зайти в суперсете в SQL lab, где создать новый запрос с этим скриптом. Там же на странице создания выбрать схему данных из 
        postgresql и таблицу. После этого нажать на run и где-то должна появиться кнопочка для создания таблички на основе этого запроса.
        !!! Это всё дело нужно сохранять как ДАТАСЕТ !!!
    2) Теперь в дашборде нужно кликнуть на круговую диаграмму, чтобы поменять ей датасет. Сменить его можно в левом верхнем углу, 
        где есть 3 точки (Chart Source -> три точки -> Swap dataset)
    3) После изменения датасета нужно сохранить график и вернуться на дашборд, где придется повторить процедуру для всех графиков и таблиц.



2) Френтенд в папке frontend
    Чтобы запустить фронтенд нужно перейти в папку с ним через терминал с помощью (cd frontend)
    После перехода в эту папку нужно прописать (npm start), после чего откроется страница в браузере (нужно подождать некоторое время)
    Если команда не выполняется из-за ошибки:
    -Ошибка ENOENT: no such file or directory указывает на то, что npm не может найти нужный файл или директорию, 
     что часто связано с отсутствием папки npm в вашем AppData\Roaming каталоге.

    Проверьте, установлены ли node и npm, выполнив следующие команды:
    node -v
    npm -v
    Если выводятся версии, то всё ок. 
    Если нет node, то нужно скачать Node.js (https://nodejs.org)
    Если нет npm, то нужно создать эту папку вручную в директории C:\Users\ABOBA\AppData\Roaming\

    Фронтенд может потребовать разрешения в брандмаэре, нужно дать разрешение для частной сети.


3) Бекенд в корневой папке проекта WEB-APP
    Чтобы запустить его, придется сначала активировать виртуальное окружение:
    - Создайте его: python -m venv .venv
    - Теперь запустите: .venv\Scripts\Activate 
    Теперь когда у вас появилась приписка "(.venv)" в терминале, можно скачать библиотеки из файла requirements.txt 
    для занесения их в свое виртуальное окружение.

    После закачки всех библиотек можно запустить бекенд командой:

    python app.py








Теперь можно всем пользоваться.
