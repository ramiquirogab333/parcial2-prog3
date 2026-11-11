#!/usr/bin/env bash
# Captura la evidencia de los casos D-01, D-02, D-04, D-05, D-06, D-07 y C-07.
# D-03 se toma desde afuera del VPS (ver DEPLOY.md), ANTES de correr este script,
# porque D-07 necesita que la venta de D-03 esté en los logs.
#
# Uso, en el VPS y desde la raíz del repositorio:
#   bash scripts/capturar_evidencia.sh
#
# Variables configurables (por si cambia el nombre o el puerto):
#   APP=grupo11-libreria-api PORT=8011 ENV_FILE=/root/grupo11-libreria.env \
#     bash scripts/capturar_evidencia.sh
set -u

APP="${APP:-grupo11-libreria-api}"
NETWORK="${NETWORK:-grupo11-libreria-net}"
ENV_FILE="${ENV_FILE:-/root/grupo11-libreria.env}"
PORT="${PORT:-8011}"
BASE="http://127.0.0.1:${PORT}"
OUT="evidence"
mkdir -p "$OUT"

for _ in $(seq 1 30); do
  estado=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}sin-health{{end}}' "$APP" 2>/dev/null || echo "no-existe")
  [ "$estado" = "healthy" ] && break
  sleep 2
done
echo "Estado de $APP: $estado"
if [ "$estado" != "healthy" ]; then
  echo "El contenedor no está healthy; abortando."
  exit 1
fi

if ! curl -fsS "$BASE/ventas/1" >/dev/null 2>&1; then
  echo "ERROR: no existe la venta 1 en la base."
  echo "Ejecutá primero el caso D-03 desde tu PC (POST /ventas/) y volvé a correr este script."
  exit 1
fi

# D-01: imagen base y imagen del proyecto.
{
  echo '$ docker images python:3.12-alpine'
  docker images python:3.12-alpine
  echo
  echo '$ docker images grupo11-libreria-api'
  docker images grupo11-libreria-api
} > "$OUT/D-01_docker_images.txt" 2>&1

# D-02: contenedor healthy y arranque en los logs.
{
  echo '$ docker ps'
  docker ps
  echo
  echo '$ docker logs '"$APP"
  docker logs "$APP" 2>&1 | head -40
} > "$OUT/D-02_contenedor_healthy.txt" 2>&1

# D-07: la venta de D-03 y el aviso del comprobante, con timestamps.
{
  echo '$ docker logs -t '"$APP"' | grep -E "POST /ventas|Comprobante" | sort'
  docker logs -t "$APP" 2>&1 | grep -E 'POST /ventas|Comprobante' | sort
} > "$OUT/D-07_comprobante.txt" 2>&1

# D-04: eliminar el contenedor, correrlo de nuevo y verificar que los datos siguen.
{
  echo '$ docker rm -f '"$APP"
  docker rm -f "$APP"
  echo
  echo '$ docker run ... (el mismo comando de DEPLOY.md)'
  docker run -d --name "$APP" \
    --network "$NETWORK" \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -p "${PORT}:8000" \
    grupo11-libreria-api:latest
  echo
  for _ in $(seq 1 30); do
    estado=$(docker inspect --format '{{.State.Health.Status}}' "$APP" 2>/dev/null || echo starting)
    [ "$estado" = "healthy" ] && break
    sleep 2
  done
  echo "estado: $estado"
  echo
  echo '$ docker ps --filter name=grupo11-libreria'
  docker ps --filter name=grupo11-libreria
  echo
  echo '$ curl -s '"$BASE"'/libros/'
  curl -s "$BASE/libros/"
} > "$OUT/D-04_recreacion.txt" 2>&1

# D-05: sin DATABASE_URL el contenedor no queda sirviendo.
{
  echo '$ docker run --rm '"${APP}"'-sin-db (sin --env-file)'
  docker run --rm --name "${APP}-sin-db" --network "$NETWORK" grupo11-libreria-api:latest
  echo "exit=$?"
} > "$OUT/D-05_sin_database_url.txt" 2>&1

# D-06: el proceso no corre como root.
{
  echo '$ docker exec '"$APP"' id'
  docker exec "$APP" id
} > "$OUT/D-06_usuario.txt" 2>&1

# C-07: contenedor temporal con SQL_ECHO=true, sin healthcheck.
grep -v '^SQL_ECHO=' "$ENV_FILE" > /root/grupo11-libreria-echo.env
echo 'SQL_ECHO=true' >> /root/grupo11-libreria-echo.env
chmod 600 /root/grupo11-libreria-echo.env
docker rm -f "${APP}-echo" >/dev/null 2>&1 || true
docker run -d --name "${APP}-echo" \
  --network "$NETWORK" \
  --env-file /root/grupo11-libreria-echo.env \
  --no-healthcheck \
  -p "127.0.0.1:8012:8000" \
  grupo11-libreria-api:latest >/dev/null

for _ in $(seq 1 30); do
  curl -fsS http://127.0.0.1:8012/health/live >/dev/null 2>&1 && break
  sleep 1
done

{
  echo "Caso C-07 - Detalle de un libro y de una venta"
  echo "Evidencia tomada en el VPS sobre la imagen desplegada, con SQL_ECHO=true."
  echo "Se cuentan las sentencias SELECT que emite SQLAlchemy para cada request."
  echo
  capturar() {
    local label="$1" url="$2" since n
    sleep 0.3
    since=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    curl -s "$url" >/dev/null
    sleep 0.6
    n=$(docker logs --since "$since" "${APP}-echo" 2>&1 | grep -c 'sqlalchemy.engine.Engine SELECT')
    echo "$label -> $n SELECT"
    docker logs --since "$since" "${APP}-echo" 2>&1 | grep 'sqlalchemy.engine.Engine SELECT'
    echo
  }
  capturar "libro 1 (1 autor)" "http://127.0.0.1:8012/libros/1"
  capturar "libro 3 (2 autores)" "http://127.0.0.1:8012/libros/3"
  capturar "venta 1 (2 renglones)" "http://127.0.0.1:8012/ventas/1"
} > "$OUT/C-07_consultas_vps.txt" 2>&1

docker rm -f "${APP}-echo" >/dev/null 2>&1 || true
rm -f /root/grupo11-libreria-echo.env

echo "Evidencia generada en $OUT/:"
ls -1 "$OUT"
