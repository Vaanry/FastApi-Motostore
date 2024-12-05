FROM nginx:1.25

# Удаляем конфигурацию Nginx по умолчанию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем ваш файл конфигурации store.conf
COPY store.conf /etc/nginx/conf.d/

# Убедимся, что Nginx не завершает работу сразу, добавив нужную команду для контейнера
CMD ["nginx", "-g", "daemon off;"]