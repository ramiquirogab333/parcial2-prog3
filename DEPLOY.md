# DEPLOY.md — Despliegue en el VPS

## Datos del despliegue

- **URL pública:** <https://libros.francogagliardi.me>
- **Fecha y hora:** 2026-11-11, 19:30 hs (UTC-3). Build iniciado a las
  22:30:04 GMT y finalizado a las 22:30:56 GMT.
- **Servidor:** `srv1920450` (Ubuntu 24.04, Docker 29.7.1), VPS compartido entre grupos
- **Grupo:** 11
- **Proyecto Easypanel:** `grupo_11`
- **Servicio de la API:** `libreria-api` (App service de Easypanel; contenedor Swarm
  `grupo_11_libreria-api.1.<id>`)
- **Servicio de PostgreSQL:** `libreria-bd` (contenedor Swarm
  `grupo_11_libreria-bd.1.<id>`), imagen `postgres:18`
- **Dominio:** `libros.francogagliardi.me`, puerto del contenedor **8000**, HTTPS
  con Let's Encrypt (Traefik de Easypanel)
- **Variables:** `DATABASE_URL` y `SQL_ECHO=false`, cargadas en Easypanel. No hay
  archivo `.env` en el repositorio ni dentro de la imagen.

> La consigna pide PostgreSQL 16 como versión mínima. Se usó `postgres:18`, que
> la supera y es compatible con el proyecto.

## Arquitectura

La imagen de la API se construye con el `Dockerfile` del repositorio
(`python:3.12-alpine`) y se ejecuta como **App service de Easypanel**, que corre
sobre Docker Swarm. PostgreSQL es un **servicio de Easypanel** del mismo
proyecto, en la red interna; su puerto 5432 **no se publica**.

El tráfico público entra por el proxy de Easypanel (Traefik) en 80/443, con
certificado de Let's Encrypt, y se enruta a la API en el puerto **8000**.

La API se conecta a la base por el host interno que muestra Easypanel, nunca por
`localhost`: dentro del contenedor, `localhost` es el propio contenedor.

## Cómo se desplegó

1. **PostgreSQL** en Easypanel: servicio `libreria-bd`, base `libreria`, imagen
   `postgres:18`, con un usuario y una contraseña definidos en el panel.
2. **App service** `libreria-api` en el proyecto `grupo_11`:
   - Fuente: GitHub `ramiquirogab333/parcial2-prog3`, rama `main`, build path `/`.
   - Build: **Dockerfile** (path `Dockerfile`).
   - Variables de entorno:
     - `DATABASE_URL` con el driver `postgresql+asyncpg`, el usuario, la
       contraseña, el host interno y la base que muestra el servicio PostgreSQL.
     - `SQL_ECHO=false`.
   - Dominio: `libros.francogagliardi.me`, puerto del contenedor **8000**, HTTPS.
3. **Deploy** desde Easypanel (build + creación del servicio).
4. **Datos iniciales** dentro del contenedor:

   ```bash
   docker exec <contenedor> python -m app.seed
   ```

## Comandos

### Build de la imagen

Easypanel ejecuta el equivalente a:

```bash
docker build -t grupo11-libreria-api:latest .
```

El `Dockerfile` parte de `python:3.12-alpine`, copia e instala `requirements.txt`
antes del código, crea el usuario `appuser` (UID 10001) y deja el `HEALTHCHECK`
sobre `http://127.0.0.1:8000/health/ready`.

### Ejecución con `docker run` (caso D-05)

La imagen no arranca sin `DATABASE_URL`:

```bash
docker run --rm --name libreria-api-sin-db easypanel/grupo_11/libreria-api:latest
# exit=1: DATABASE_URL es obligatoria
```

La salida completa está en `evidence/D-05_sin_database_url.txt`.

### Ejecución manual equivalente (validación local)

El despliegue en línea se hace con Easypanel, pero la imagen también se validó
localmente con el mismo comando que pide la consigna:

```bash
docker run -d --name grupo11-libreria-api \
  --env-file /root/grupo11-libreria.env \
  -p 8011:8000 \
  grupo11-libreria-api:latest
```

El archivo `grupo11-libreria.env` contiene `DATABASE_URL` y `SQL_ECHO`; vive
fuera del repositorio y de la imagen. Su contenido no se incluye en este
documento.

### Datos iniciales

```bash
docker exec <contenedor> python -m app.seed
```

Es idempotente: si ya hay libros cargados, no duplica nada.

### Verificación

```bash
curl -i https://libros.francogagliardi.me/health/ready
curl -s https://libros.francogagliardi.me/libros/
docker ps --filter name=grupo_11_libreria-api
docker logs <contenedor>
```

## Cómo se actualiza la aplicación

1. Se hace `push` a la rama `main` del repositorio.
2. En Easypanel, se entra al App service `libreria-api` y se elige
   **Deploy** (o **Redeploy**). Easypanel reconstruye la imagen con el
   `Dockerfile` y recrea el contenedor.
3. Los datos **no se pierden**: viven en el servicio PostgreSQL, no en el
   contenedor de la API.
4. Si se agregaron datos iniciales nuevos, se puede volver a ejecutar
   `docker exec <contenedor> python -m app.seed`; el script no duplica.
5. El arranque vuelve a ejecutar `SQLModel.metadata.create_all`: solo crea las
   tablas que faltan y no altera las existentes.

## Cambios al proyecto para que corra en el contenedor

- `DATABASE_URL` es obligatoria: no hay valores por defecto en el código. Si
  falta, la aplicación no arranca (caso D-05).
- La variable de diagnóstico es `SQL_ECHO` (en producción, `false`).
- El `HEALTHCHECK` consulta `http://127.0.0.1:8000/health/ready` y no
  `localhost`, porque en Alpine `localhost` resuelve primero a IPv6 (`::1`) y
  uvicorn escucha en IPv4.
- `GET /health/live` devuelve `{"estado":"vivo"}`, como en la tabla de endpoints.
- Los datos iniciales se cargan con `python -m app.seed` dentro del contenedor.
- `GET /` no está definido y devuelve 404. La documentación interactiva está en
  `/docs`; los endpoints de la consigna están bajo `/health`, `/editoriales`,
  `/generos`, `/autores`, `/libros`, `/clientes` y `/ventas`.

## Nota sobre el criterio "Contenedor: la imagen"

La imagen se construye con `python:3.12-alpine` y el `Dockerfile` del proyecto;
la aplicación corre con el usuario sin privilegios `appuser` (UID 10001), sin
secretos dentro de la imagen y con `HEALTHCHECK`. El servicio en línea es
administrado por Easypanel (Docker Swarm), por lo que el contenedor de
producción no se lanza con `docker run`; el comando `docker run` se usa en D-05
para demostrar que la imagen no arranca sin `DATABASE_URL`. La evidencia de
cada caso está en `evidence/`.

## Evidencia

| Caso | Archivo | Resultado |
| --- | --- | --- |
| C-07 | `evidence/C-07_consultas.txt` | 2 SELECT fijas para un libro con 1 autor, con 2 autores y para una venta con 2 renglones |
| D-01 | `evidence/D-01_docker_images.txt` | `python:3.12-alpine` 74.8 MB; imagen del proyecto 209 MB |
| D-02 | `evidence/D-02_contenedor_healthy.txt` y `evidence/D-02_build_log.txt` | Build con Dockerfile, contenedor `healthy` y arranque con las tablas creadas |
| D-03 | `evidence/D-03_url_publica.txt` | `/health/ready` 200, `/libros/` 200 y `POST /ventas/` 201 |
| D-04 | `evidence/D-04_recreacion.txt` | Se elimina la tarea y Swarm la recrea `healthy`; los datos siguen |
| D-05 | `evidence/D-05_sin_database_url.txt` | Sin `DATABASE_URL` el contenedor termina con `exit=1` |
| D-06 | `evidence/D-06_usuario.txt` | `uid=10001(appuser)`, no root |
| D-07 | `evidence/D-07_comprobante.txt` | El comprobante aparece 0.5 s después de la respuesta 201 |
