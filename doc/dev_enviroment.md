# Development окружение 

Dev-окружение необходимо для локальной разработки и тестирования фич.

## Компоненты окружения
1. Приложение `pl-app` - Python приложение, выполняющее основную логику для бронирования встреч
2. База данных `pl-db` - База данных Postgres, в которой хранятся данные приложения
3. Клиент для работы с Postgres PgAdmin `pl-pgadmin` - предоставляет инструментарий для работы с БД Postgres. Позволяет 
подключаться к БД, выполнять SQL-настройки, администрировать и мониторить Postgres

## Развертывание dev-окружения
1. Cоздать `docker/docker-compose.override.yml` файл с помощью команды
`cp docker/docker-compose.override.yml.example docker/docker-compose.override.yml`
2. Поднять окружение с помощью команды `bin/pl-dev-up`
3. Зайти в pgadmin: `http://localhost:5050`. Логин и пароль см. в `docker/docker-compose.yml`
4. При первом входе в PgAdmin потребуется ввести пароль

## Очистка dev-окружения и удаление данных
1. Выполнить `bin/etl-dev-down` для того чтобы остановить все docker-контейнеры
2. Выполнив команду `docker volume rm docker_pl-db-data docker_pl-pgadmin-data`, будут удалены все volume-ы docker контейнеров.
Внимание!! эта команда удаляет все данные, которые ранее были записаны в БД

## Как подключиться к Postgres в pgadmin
1. Открываем окно подключения к серверу `Add New Server`
2. В `General` в поле `Name` прописываем любое название сервера
3. Во вкладке `Connection` указываем следующее:
   - `Host Name/address` - указываем имя `pl-db` (название docker-контейнера)
   - `Port` - `5432` (оставляем по умолчанию)
   - `Maintenance database` - `planify`
   - `Username` - admin
   - `Password` - qwerty

## Обновление docker-контейнера c Python-приложением
Обновление docker-контейнера необходимо выполнять, если были добавлены новые зависимости в проект. Таким образом, после 
добавления зависимостей в файл `pyproject.toml`, необходимо собрать новую версию docker-контейнера командой `bin/pl-dev-build-images`