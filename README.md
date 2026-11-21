# Why&What

**Кулаков Никита Сергеевич, Web-13**  
Учебный сайт вопросов и ответов на Django и PostgreSQL.

[VK education](https://education.vk.company/profile/nik.kulakov/) · [Условия ДЗ4](https://github.com/Highoc/web-tasks/blob/master/homeworks/markdown/task-4.md)

## Что работает

- Регистрация, вход с безопасным `next`, выход и редактирование профиля.
- Добавление вопросов с тегами и ответов; пагинация и переход к новому ответу.
- Лайки и дизлайки через AJAX. Выбранная оценка блокируется, противоположной можно сменить голос.
- Выбор правильного ответа только автором вопроса.
- Необязательные аватары PNG/JPEG до 5 МБ, уникальные имена файлов и заглушка при отсутствии.
- Проверка данных в формах, сообщения об ошибках, CSRF и ограничения для гостей.
- nginx перед Django: самостоятельно раздаёт стили и аватары.

Авторизация находится в приложении `users`, а не в `core`, указанном в п. 4.2 ДЗ. После выхода с публичной страницы её адрес сохраняется; из закрытого профиля выполняется переход на главную.

## Первый запуск

Нужен запущенный Docker. Все команды выполняются из корня проекта, рядом с `docker-compose.yaml`.

1. Скопируйте пример настроек:

   ```bash
   cp .env.example .env.docker
   ```

2. В `.env.docker` замените `SECRET_KEY` и `POSTGRES_PASSWORD` своими значениями. Остальные настройки уже подходят для Docker: `DB_HOST=db`, `DB_PORT=5432`. Файл с секретами исключён из Git.

3. Запустите контейнеры, примените миграции и создайте администратора:

   ```bash
   docker compose up -d --build
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

Откройте [сайт](http://localhost:8000/) или [админку](http://localhost:8000/admin/). Для обычного пользователя используйте регистрацию на сайте.

Следующий запуск: `docker compose up -d`. Остановка: `docker compose down`. База и аватары сохраняются в Docker volumes. Изменение пароля в `.env.docker` не меняет пароль уже созданной базы.

## Тестовые данные

После миграций можно наполнить базу:

```bash
docker compose exec web python manage.py fill_db 10
```

Параметр `ratio` должен быть не меньше 2. Команда добавляет `ratio` пользователей и тегов, `ratio × 10` вопросов, `ratio × 100` ответов и `ratio × 200` голосов. Повторный запуск добавляет новые записи.

Для объёма из ДЗ3 используйте `fill_db 10000`: это длительное создание 10 тысяч пользователей, 100 тысяч вопросов и миллиона ответов. Тестовые пользователи не могут входить на сайт; используйте свой аккаунт или администратора.

## nginx и статика

Конфигурация: [nginx/default.conf](nginx/default.conf). Внешний порт `8000` принадлежит nginx, Django доступен ему внутри Docker как `web:8000`. Общие volumes `static` и `media` позволяют nginx читать стили и аватары. Статика собирается автоматически при запуске `web`.

После изменения CSS выполните:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

После изменения конфигурации nginx проверьте её и перезагрузите:

```bash
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

После изменения `.env.docker` выполните `docker compose up -d`, затем перезагрузите nginx командой выше. Логи: `docker compose logs -f web nginx`.

## Проверка ДЗ4

Проверьте регистрацию, вход и выход, профиль, загрузку аватара, создание вопроса и не менее пяти ответов. Новый ответ должен открыться на своей странице. Под двумя аккаунтами проверьте оценки и выбор правильного ответа; гостю недоступные кнопки показываются отключёнными с подсказками.

AJAX отправляется на `/question/<id>/` с параметром `action`: `vote_question`, `vote_answer` или `correct_answer`. Скрипт находится в [actions.html](web-edu/questions/templates/questions/includes/actions.html), сервер возвращает JSON, ошибки показываются через `alert`.

Запуск тестов на отдельной PostgreSQL-базе:

```bash
docker compose exec -e DEBUG=False web python manage.py test users questions
```
