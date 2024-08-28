# SQLALCHEMY

# Размер пула - это максимальное количество поддерживаемых постоянных подключений.
pool_size=5,

# Временно превышает установленный размер пула, если подключения недоступны.
max_overflow=2,

# Общее количество одновременных подключений для вашего приложения составит
# общее значение pool_size и max_overflow.
# 'pool_timeout' - это максимальное количество секунд ожидания при получении
# нового соединения из пула. По истечении указанного периода времени будет выдано
# исключение.
pool_timeout=30, # 30 секунд

# GIT
# удаление директории со всеми вложенными файлами из гита
git rm -r --cached directory_name


# ALEMBIC
## Создание ревизии
alembic revision --autogenerate -m "revision"
## Применение изменений ревизии к базе
alembic upgrade revision_id
## Обновление до последней ревизии
alembic upgrade head
## Откат к предыдущей ревизии
alembic downgrade -1
## Откат к началу
alembic downgrade base





# ГОТОВЫЕ КОМАНДЫ ДЛЯ РАЗВЕРТЫВАНИЯ КОНТЕЙНЕРОВ

# удаление всех образов
docker image prune -a

docker run --name pg \
-e POSTGRES_USER=admin \
-e POSTGRES_PASSWORD=somepass \
-v pg_data:/var/lib/postgresql \
-p 5432:5432 -d \
--restart always \
--network appnet \
postgres

docker run --name adminer -p 8080:8080 -d --restart always --network appnet adminer
# развертываем redis и rabbit перед запуском воркера
docker run --name redis -d -v redis_data:/var/lib/redis -p 6379:6379 --restart always --network appnet redis
docker run --name rabbit_mq -d -p 5672:5672 -e RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS"-rabbit consumer_timeout 36000000" rabbitmq

docker run -d --name prometheus -p 9090:9090 -v prometheus-data:/prometheus prom/prometheus
docker run -d --name grafana -p 3000:3000 -v grafana-data:/var/lib/grafana grafana/grafana
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 -v rabbitmq-data:/var/lib/rabbitmq rabbitmq:management

docker volume create portainer_data
docker run -d -p 9000:9000 --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce

docker run -d -p 9443:9443 -p 7000:8000 \
    --name portainer --restart always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v portainer_data:/data \
    -v /home/user/nginx/certs:/certs \
    --network appnet \
    portainer/portainer-ce:2.20.3 \
    --sslcert /certs/certificate.crt \
    --sslkey /certs/private.key
    

docker run -p 9000:9000 \
           -p 9001:9001 \
           --name minio \
           -v minio_data:/var/lib/minio \
           -e "MINIO_ROOT_USER=admin" \
           -e "MINIO_ROOT_PASSWORD=somepass" \
           quay.io/minio/minio server /data --console-address ":9001"


docker run -d -p 80:80 --name nginx --restart=always \
-v ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
-v ./nginx/certs:/etc/nginx/certs:ro \
nginx:latest

- :ro: Этот флаг указывает на то,
- что монтируемый том доступен только для чтения (read-only).
- То есть контейнер сможет читать файл, но не сможет его изменять.

docker run -d \
--name nginx \
--network appnet \
-p 443:443 \
-p 80:80 \
-v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf \
-v $(pwd)/nginx/certs:/certs \
-v frontend_build:/usr/share/nginx/html \
nginx:latest

# рестарт nginx без перезапуска контейнера:
docker exec frontend nginx -s reload

# команда, которая проверяет, что конфиг nginx заполнен корректно:
docker exec nginx nginx -t

# Генерим сертификаты
openssl req -newkey rsa:2048 -sha256 -nodes -x509 -days 365 \
-keyout SSL_PRIVATE.key \
-out SSL_PUBLIC.crt \
-subj "/C=RU/ST=Moscow/L=Moscow/O=Country Balls Inc/CN=server_ip"
# Конвертим в pem
openssl x509 -in SSL_PUBLIC.crt -out SSL_PUBLIC.pem -outform PEM


# Настройка minio для постоянных ссылок
Создаешь бакет и делаешь его публичным. Все


# await bot.delete_webhook()
# - так делать не рекомендуется https://habr.com/ru/articles/819955/#comment_26908387