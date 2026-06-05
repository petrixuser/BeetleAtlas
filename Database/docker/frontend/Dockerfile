FROM nginx:alpine

COPY docker/frontend/entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY Database/frontend/ /usr/share/nginx/html/

EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
