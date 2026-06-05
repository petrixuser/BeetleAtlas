FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY Database/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY Database/backend/ /app/
COPY docker/backend/entrypoint.sh /docker-entrypoint.backend.sh
RUN chmod +x /docker-entrypoint.backend.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.backend.sh"]
