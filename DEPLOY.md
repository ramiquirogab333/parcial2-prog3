# DEPLOY.md — Despliegue en el VPS

## Datos del despliegue

- **URL pública:** `http://libros.francogagliardi.me:8011`
- **Fecha y hora del despliegue:** PENDIENTE (se completa al desplegar)
- **Servidor:** `srv1920450` (Ubuntu 24.04, Docker 29.7.1), VPS compartido entre grupos
- **Grupo:** 11
- **Contenedor de la API:** `grupo11-libreria-api`
- **Contenedor de PostgreSQL:** `grupo11-libreria-db` (`postgres:16-alpine`)
- **Red interna:** `grupo11-libreria-net`
- **Volumen de datos:** `grupo11-libreria-pgdata`
- **Archivo de variables:** `/root/grupo11-libreria.env` (fuera del repositorio y
  de la imagen; permisos `600`)

> Los recursos son propios del grupo 11. No se reutilizan ni se modifican
> `libreria`, `libreria-db` ni `libreria-net`, que pertenecen a otro grupo del
> mismo servidor.

## Arquitectura

La imagen de la aplicación se construye en el servidor a partir del `Dockerfile`.
PostgreSQL **no forma parte de la imagen ni del contenedor de la API**: corre en
su propio contenedor `postgres:16-alpine`, con un volumen para que los datos
sobrevivan a la recreación de la API. Solo se publica el puerto de la API; el
puerto 5432 de PostgreSQL queda en la red interna y no se publica.

La API se conecta por el nombre del contenedor de la base
(`grupo11-libreria-db`) dentro de la red `grupo11-libreria-net`. No se usa
`localhost`: dentro de un contenedor, `localhost` es el propio contenedor.

## Comandos

### 1. Código en el servidor

```bash
cd /root
git clone https://github.com/ramiquirogab333/parcial2-prog3.git grupo11-libreria-src
cd grupo11-libreria-src
```

En actualizaciones posteriores:

```bash
cd /root/grupo11-libreria-src
git pull
```

### 2. Red y volumen

```bash
docker network create grupo11-libreria-net 2>/dev/null || true
docker volume create grupo11-libreria-pgdata
```

### 3. Variables de entorno y PostgreSQL (primera vez)

El archivo de variables se crea en el servidor, fuera del repositorio. La
contraseña se escribe una sola vez y no queda en el historial de comandos.

**Usar solo letras y números** en la contraseña (sin `@`, `:`, `/`, `#` ni `%`),
para que no haya que escaparla dentro de la URL.

```bash
read -rsp "Password de PostgreSQL: " DB_PASS; echo
printf 'DATABASE_URL=postgresql+asyncpg://libreria:%s@grupo11-libreria-db:5432/libreria\nSQL_ECHO=false\n' "$DB_PASS" > /root/grupo11-libreria.env
chmod 600 /root/grupo11-libreria.env

docker run -d --name grupo11-libreria-db \
  --network grupo11-libreria-net \
  --restart unless-stopped \
  -e POSTGRES_USER=libreria \
  -e POSTGRES_PASSWORD="$DB_PASS" \
  -e POSTGRES_DB=libreria \
  -v grupo11-libreria-pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

unset DB_PASS
```

### 4. Imagen de la aplicación

```bash
docker build -t grupo11-libreria-api:latest .
```

### 5. Contenedor de la aplicación

```bash
docker run -d --name grupo11-libreria-api \
  --network grupo11-libreria-net \
  --restart unless-stopped \
  --env-file /root/grupo11-libreria.env \
  -p 8011:8000 \
  grupo11-libreria-api:latest
```

Verificación:

```bash
docker ps --filter name=grupo11-libreria
docker inspect --format '{{.State.Health.Status}}' grupo11-libreria-api
docker logs grupo11-libreria-api
```

El contenedor queda `healthy` cuando `GET /health/ready` responde 200 (es decir,
cuando PostgreSQL responde). Si la base todavía no estaba lista, el
`--restart unless-stopped` vuelve a levantar la API.

### 6. Datos iniciales

```bash
docker exec grupo11-libreria-api python -m app.seed
```

El script es idempotente: si ya hay libros cargados, no duplica nada.

### 7. Prueba desde el servidor y desde afuera

```bash
curl -i http://127.0.0.1:8011/health/ready
curl -s http://127.0.0.1:8011/libros/
```

Desde otra máquina:

```bash
curl -i http://libros.francogagliardi.me:8011/health/ready
curl -s http://libros.francogagliardi.me:8011/libros/
```

## Cómo se actualiza la aplicación

Los datos viven en el volumen `grupo11-libreria-pgdata`, no en el contenedor de
la API. Por eso se puede eliminar y recrear el contenedor sin perder datos:

```bash
cd /root/grupo11-libreria-src
git pull
docker build -t grupo11-libreria-api:latest .
docker rm -f grupo11-libreria-api
docker run -d --name grupo11-libreria-api \
  --network grupo11-libreria-net \
  --restart unless-stopped \
  --env-file /root/grupo11-libreria.env \
  -p 8011:8000 \
  grupo11-libreria-api:latest
docker exec grupo11-libreria-api python -m app.seed   # opcional; no duplica
```

El arranque vuelve a ejecutar `SQLModel.metadata.create_all`: solo crea las
tablas que faltan y no altera las existentes.

## Cambios al proyecto para que corra en el contenedor

- `DATABASE_URL` es obligatoria: no hay valores por defecto en el código. Si
  falta, la aplicación no arranca (caso D-05).
- La variable que activa el diagnóstico de consultas es `SQL_ECHO` (en
  producción va en `false`).
- El `HEALTHCHECK` consulta `http://127.0.0.1:8000/health/ready` y no
  `localhost`, porque en Alpine `localhost` resuelve primero a IPv6 (`::1`) y
  uvicorn escucha en IPv4.
- `GET /health/live` devuelve `{"estado":"vivo"}`, como en la tabla de endpoints
  de la consigna.
- Los datos iniciales se cargan con `python -m app.seed` dentro del contenedor.

## Alternativa: PostgreSQL creado desde Easypanel

Si se prefiere crear el PostgreSQL como servicio del proyecto `grupo_11` en
Easypanel, el contenedor de la API solo puede alcanzarlo si la red
`easypanel-grupo_11` es `attachable` (`docker network inspect
easypanel-grupo_11 --format '{{.Attachable}}'`) y se corre la API con
`--network easypanel-grupo_11`. El host interno y las credenciales son los que
muestra Easypanel. La opción documentada arriba (contenedor propio) no depende
de la red de Easypanel y es la que se usa para la entrega.

## Evidencia

Las salidas de los casos D-01 a D-07 y C-07 se guardan en `evidence/`.
Ver la tabla de evidencia al final del archivo una vez desplegado.
