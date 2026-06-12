FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/App/core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app/backend
COPY backend/docker/entrypoint.sh /docker-entrypoint.backend.sh
RUN sed -i 's/\r$//' /docker-entrypoint.backend.sh && chmod +x /docker-entrypoint.backend.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.backend.sh"]
