# Imagen del proyecto - Parcial Cap. 1 a 4 (librería de barrio)
# Base obligatoria: python:3.12-alpine (la consigna fija el límite de 100 MB
# para la imagen base; slim no cumple).
FROM python:3.12-alpine

# Sin archivos .pyc y con logs sin buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Las dependencias se copian e instalan antes del código: mientras no cambien,
# esta capa sale de la caché y un cambio de código no reinstala todo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Solo el código de la aplicación. El .env, el .git, el .venv y los .pyc
# quedan afuera por .dockerignore: nada de eso se hornea en la imagen.
COPY app ./app

# La aplicación no corre como root: si vulneran la API, no son dueños del
# contenedor. UID fijo para que la evidencia (docker exec ... id) sea estable.
RUN adduser -D -H -u 10001 appuser
USER appuser

# Dentro del contenedor uvicorn escucha en 0.0.0.0; 127.0.0.1 solo se alcanza
# desde adentro y el puerto publicado nunca respondería.
EXPOSE 8000

# Alpine no trae curl; wget sí. Se usa 127.0.0.1 (no localhost) porque en
# Alpine localhost resuelve primero a ::1 (IPv6) y uvicorn escucha en IPv4.
# /health/ready devuelve 503 si PostgreSQL no responde, así que wget falla.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8000/health/ready > /dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
