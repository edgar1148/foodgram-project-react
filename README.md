## Описание 

Вам предстоит поработать с проектом «Фудграм» — сайтом, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
---

### База данных

PostgreSQL

Шаблон для заполнения файла '.env':
```python
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='Секретный ключ'
ALLOWED_HOSTS='Имя или IP хоста'
```
---
### Для запуска

Клонируем проект:
```bash
HTTPS: git clone https://github.com/edgar1148/foodgram-project-react.git
SSH: git clone git@github.com:edgar1148/foodgram-project-react.git
```
Создаем и активируем виртуальное окружение:
```bash
python -m venv venv
```
```bash
source venv/Scripts/activate
```
Устанавливаем зависимости из файла requirements.txt:
```bash
pip install -r requirements.txt
```
Локально собираем образы и запускаем:
```bash
docker compose up --build
```

### Создание Docker-образов

1. Замените `username` на свой логин на DockerHub:

    ```
    cd frontend
    docker build -t username/foodgram_frontend .
    cd ../backend
    docker build -t username/foodgram_backend .
    cd ../gateway
    docker build -t username/foodgram_gateway . 
    ```

2. Загрузите образы на DockerHub:

    ```
    docker push username/foodgram_frontend
    docker push username/foodgram_backend
    docker push username/foodgram_gateway
    ```

После отправки образов на сервере создать и запустить контейнеры:
```bash
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml up -d
```
Выполняем миграции:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
Собираем статику:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
Создаем суперюзера:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```
Загружаем ингредиенты из файла командой:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients
```
Открываем проект по адресу [https://foodgramedgar1148.hopto.org](https://foodgramedgar1148.hopto.org/)
---

### Технологии
Python 3.9.10,
Django 4.2.6,
djangorestframework==3.14.0, 
PostgreSQL 13.10

### Автор
[Евгений Екишев - edgar1148](https://github.com/edgar1148)
