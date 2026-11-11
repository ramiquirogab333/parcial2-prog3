# Librería de Barrio API

API asincrónica para el catálogo y las ventas de una librería de barrio.
Parcial de Programación III (capítulos 1 a 4) con empaquetado en Docker y
despliegue en un VPS.

## Integrantes

| Integrante | Turno |
| --- | --- |
| Emmanuel Miranda | 1. Core, base de datos y health |
| Santiago Copia | 2. Editoriales y géneros |
| Ignacio Ceballos | 3. Autores y clientes |
| Ciro Cattaneo | 4. Libros y autorías |
| Ramiro Quiroga | 5. Ventas |
| Franco Gagliardi | 6. Docker, VPS y despliegue |

## Stack

- Python 3.12
- FastAPI 0.111 (todos los handlers con `async def`)
- SQLModel 0.0.24 y SQLAlchemy 2.0 asincrónico
- PostgreSQL 16 con el controlador `asyncpg` 0.30
- uvicorn

## Requisitos previos

- Python 3.12
- PostgreSQL 16 (local o en el servidor)
- Docker 20.10 o superior (solo para construir la imagen)

## Puesta en marcha desde cero (máquina local)

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone https://github.com/ramiquirogab333/parcial2-prog3.git
   cd parcial2-prog3
   ```

2. Crear y activar el entorno virtual.

   Windows (PowerShell):

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Linux / macOS:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crear la base en PostgreSQL 16 (si no existe):

   ```bash
   psql -U postgres -c "CREATE DATABASE libreria;"
   ```

5. Crear el archivo `.env` a partir de `env.example` y completar `DATABASE_URL`.

   Windows:

   ```powershell
   Copy-Item env.example .env
   ```

   Linux / macOS:

   ```bash
   cp env.example .env
   ```

   Ejemplo para una base local:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/libreria
   SQL_ECHO=false
   ```

   El `.env` no se versiona: cada máquina usa sus propias credenciales.

6. Arrancar el servidor. Al iniciar, el `lifespan` crea las tablas que falten
   con `SQLModel.metadata.create_all`:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Cargar los datos iniciales (editoriales, géneros, autores, libros y
   clientes). El script es idempotente: si ya hay libros, no duplica nada.

   ```bash
   python -m app.seed
   ```

8. Verificar que responde:

   - Documentación interactiva: <http://127.0.0.1:8000/docs>
   - Salud: <http://127.0.0.1:8000/health/ready>

## Casos de prueba

La carpeta `test/` contiene archivos `.http` con los casos de la consigna y el
resultado esperado en cada comentario. Se ejecutan con la extensión
**REST Client** de VS Code, con la API corriendo en `127.0.0.1:8000`.

Los archivos asumen una base limpia: algunos crean sus propios prerrequisitos
(editorial, género, autores, cliente) antes de probar el módulo.

## Docker

Construir la imagen (desde la raíz del proyecto):

```bash
docker build -t libreria:latest .
```

Correr el contenedor con las variables desde un archivo externo (nunca dentro
de la imagen):

```bash
docker run -d --name libreria -p 127.0.0.1:8000:8000 \
  --env-file libreria.env libreria:latest
```

Cargar los datos iniciales dentro del contenedor:

```bash
docker exec libreria python -m app.seed
```

## Despliegue

El despliegue real en el VPS, la URL pública y los comandos completos están
documentados en [`DEPLOY.md`](DEPLOY.md). Las salidas de diagnóstico pedidas
por la consigna están en la carpeta [`evidence/`](evidence/).

## Estructura del proyecto

```text
app/
  main.py                 aplicación, lifespan y registro de routers
  seed.py                 datos iniciales
  core/
    config.py             lectura de DATABASE_URL
    database.py           motor asincrónico, sesión y get_session
  modules/
    health/               /health/live y /health/ready
    editoriales/          módulo editoriales
    generos/              módulo géneros
    autores/              módulo autores
    clientes/             clientes y perfil 1 a 1
    libros/               libros y libro_autor
    ventas/               ventas y renglones
test/                     casos .http
Dockerfile                imagen de la aplicación
.dockerignore             archivos que no entran a la imagen
env.example               forma de las variables de entorno
DEPLOY.md                 despliegue en el VPS
evidence/                 salidas de los casos C-07 y D-01 a D-07
```
