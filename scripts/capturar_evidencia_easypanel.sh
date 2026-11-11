#!/usr/bin/env bash
# Evidencia para el despliegue con Easypanel (Docker Swarm).
#
# Antes de correrlo:
#   1. Cargar los datos iniciales:
#        docker exec <contenedor> python -m app.seed
#   2. Ejecutar D-03 desde la PC (POST /ventas/), para que D-07 tenga la venta.
#
# Uso, en el VPS y desde la raíz del repositorio:
#   bash scripts/capturar_evidencia_easypanel.sh
#
# Si el dominio cambia:
#   PUBLIC_URL=https://otro.dominio bash scripts/capturar_evidencia_easypanel.sh
set -u

PUBLIC_URL="${PUBLIC_URL:-https://libros.francogagliardi.me}"
OUT="evidence"
mkdir -p "$OUT"

find_container() {
  docker ps --filter name=libreria-api --format '{{.Names}}' | head -1
}

APP="$(find_container)"
if [ -z "$APP" ]; then
  echo "No encontré el contenedor de libreria-api. Abortando."
  exit 1
fi
IMAGE="$(docker inspect "$APP" --format '{{.Config.Image}}')"
echo "Contenedor: $APP"
echo "Imagen: $IMAGE"

# D-01: imagen base y imagen del proyecto.
{
  echo '$ docker images python:3.12-alpine'
  docker images python:3.12-alpine
  echo
  echo "\$ docker images $IMAGE"
  docker images "$IMAGE"
} > "$OUT/D-01_docker_images.txt" 2>&1

# D-02: contenedor healthy y arranque en los logs.
{
  echo '$ docker ps'
  docker ps
  echo
  echo "\$ docker logs $APP"
  docker logs "$APP" 2>&1 | head -40
} > "$OUT/D-02_contenedor_healthy.txt" 2>&1

# D-07: venta de D-03 y aviso del comprobante, con timestamps.
{
  echo "\$ docker logs -t $APP | grep -E 'POST /ventas|Comprobante' | sort"
  docker logs -t "$APP" 2>&1 | grep -E 'POST /ventas|Comprobante' | sort
} > "$OUT/D-07_comprobante.txt" 2>&1
if ! grep -q 'Comprobante' "$OUT/D-07_comprobante.txt"; then
  echo "ADVERTENCIA: D-07 quedó vacío. Ejecutá primero D-03 desde la PC (POST /ventas/)."
fi

# D-04: recrear la tarea (Swarm) y verificar que los datos siguen.
{
  OLD="$APP"
  echo "\$ docker rm -f $OLD"
  docker rm -f "$OLD"
  NEW=""
  for _ in $(seq 1 30); do
    NEW="$(find_container)"
    if [ -n "$NEW" ] && [ "$NEW" != "$OLD" ]; then break; fi
    sleep 2
  done
  if [ -z "$NEW" ] || [ "$NEW" = "$OLD" ]; then
    echo "Swarm no recreó la tarea; forzando con docker service update --force..."
    SVC="$(docker service ls --filter name=libreria-api --format '{{.Name}}' | head -1)"
    docker service update --force "$SVC"
    for _ in $(seq 1 30); do
      NEW="$(find_container)"
      if [ -n "$NEW" ] && [ "$NEW" != "$OLD" ]; then break; fi
      sleep 2
    done
  fi
  echo "nuevo contenedor: $NEW"
  for _ in $(seq 1 30); do
    estado=$(docker inspect --format '{{.State.Health.Status}}' "$NEW" 2>/dev/null || echo starting)
    [ "$estado" = "healthy" ] && break
    sleep 2
  done
  echo "estado: $estado"
  if [ "$estado" != "healthy" ]; then
    echo "El healthcheck no reporta healthy; probando /health/ready desde el contenedor:"
    docker exec "$NEW" wget -qO- http://127.0.0.1:8000/health/ready || true
    echo
  fi
  echo
  echo '$ docker ps --filter name=libreria-api'
  docker ps --filter name=libreria-api
  echo
  echo "\$ docker exec $NEW wget -qO- http://127.0.0.1:8000/libros/"
  docker exec "$NEW" wget -qO- http://127.0.0.1:8000/libros/
} > "$OUT/D-04_recreacion.txt" 2>&1

# D-05: sin DATABASE_URL el contenedor no queda sirviendo.
{
  echo "\$ docker run --rm --name libreria-api-sin-db $IMAGE"
  docker run --rm --name libreria-api-sin-db "$IMAGE"
  echo "exit=$?"
} > "$OUT/D-05_sin_database_url.txt" 2>&1

# D-06: el proceso no corre como root.
{
  APP="$(find_container)"
  echo "\$ docker exec $APP id"
  docker exec "$APP" id
} > "$OUT/D-06_usuario.txt" 2>&1

echo "Evidencia generada en $OUT/:"
ls -1 "$OUT"
