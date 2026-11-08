# Why&What

**Кулаков Никита Сергеевич, Web-13**  
Учебный сайт вопросов и ответов на Django, ДЗ2.

[VK education](https://education.vk.company/profile/nik.kulakov/)

Страницы работают на данных-заглушках. Авторизация и сохранение форм пока не реализованы.

## Что сделано

- [base.html](web-edu/templates/base.html) — общий каркас страницы.
- [index.html](web-edu/questions/templates/questions/index.html) — список новых вопросов.
- [hot.html](web-edu/questions/templates/questions/hot.html) — список лучших вопросов.
- [tag.html](web-edu/questions/templates/questions/tag.html) — вопросы по тегу.
- [question_detail.html](web-edu/questions/templates/questions/question_detail.html) — вопрос, ответы и форма ответа.
- [ask.html](web-edu/questions/templates/questions/ask.html) — форма добавления вопроса.
- [profile.html](web-edu/users/templates/users/profile.html) — настройки профиля и выбор аватара.
- [login.html](web-edu/users/templates/users/login.html) — форма входа.
- [signup.html](web-edu/users/templates/users/signup.html) — форма регистрации с выбором аватара.

## Настройка окружения

Перед любым способом запуска скопировать `.env.example` в `.env` в корне репозитория:

```bash
cp .env.example .env
```

В Windows PowerShell: `Copy-Item .env.example .env`.

В `.env` заменить заглушку `SECRET_KEY` на собственную случайную строку и оставить `DEBUG=True` для учебного запуска. Ключ можно сгенерировать командой:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

В Windows вместо `python3` использовать `py -3.14`. Файл `.env` не добавлять в Git.

## Локальный запуск

Нужен Python 3.14. Команды выполнять из корня репозитория.

Создать и активировать виртуальное окружение (Linux / macOS / WSL):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Для Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Установить зависимости и запустить проект:

```bash
python -m pip install -r requirements.txt
cd web-edu
python manage.py runserver
```

## Запуск через Docker Compose

Нужны установленный и запущенный Docker и Docker Compose. Из корня репозитория:

```bash
docker compose up --build
```

Остановить контейнеры: Ctrl+C, затем `docker compose down`.

## Проверка

После запуска открыть [http://localhost:8000/](http://localhost:8000/).

Доступны страницы: `/`, `/hot/`, `/tag/CSS/`, `/question/1/`, `/ask/`, `/login/`, `/signup/`, `/profile/`.

Для проверки пагинации: `/?page=2` и `/question/1/?page=2`.
