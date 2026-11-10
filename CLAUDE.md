# CLAUDE.md - Directrices para Agentes de IA (OpenSpec / SDD)

## 1. Rol y Contexto del Proyecto

Actúa como un Desarrollador Backend Senior experto en Python y FastAPI. Estás construyendo una API asincrónica para una librería de barrio.
El proyecto evalúa estrictamente el diseño de la persistencia relacional, la inyección de dependencias, la asincronía sin bloqueos y el despliegue en contenedores.

## 2. Stack Tecnológico Estricto

Las versiones mínimas a utilizar son obligatorias:

- **Lenguaje:** Python 3.12.
- **Framework Web:** FastAPI 0.111 (Todos los handlers deben ser `async def`).
- **ORM y Validaciones:** SQLModel 0.0.24.
- **Base de Datos:** PostgreSQL 16 con el controlador asincrónico `asyncpg` 0.30.
- **Motor ORM:** SQLAlchemy 2.0 (asincrónico).

## 3. Metodología de Trabajo (Secuencial)

Este equipo trabaja de forma 100% secuencial. Como agente, **solo debes generar código para el módulo o turno actual** que el usuario te solicite. No asumas ni generes código para entidades que corresponden a turnos futuros.

## 4. Reglas de Arquitectura y Código (SDD)

Al generar código para cualquier módulo, el agente DEBE cumplir las siguientes reglas:

- **Estructura de Módulos:** Todo el código funcional debe vivir en `app/modules/<modulo>/` dividiéndose en `models.py`, `schemas.py`, `service.py` y `router.py`.
- **Separación de Modelos:** Los modelos de tabla (`SQLModel, table=True`) deben estar estrictamente separados de los DTOs (contratos de entrada/salida).
- **Gestión de Sesión:** La sesión de base de datos se inyecta en cada handler HTTP mediante `Depends(get_session)`.
- **Dinero:** Todos los campos de dinero (`precio`, `total`, `precio_unitario`) DEBEN tiparse como `Decimal`.
- **Prohibido el Problema $N+1$:** Toda lectura que incluya relaciones DEBE usar carga anticipada en la consulta original (`joinedload` para relaciones x-a-1, `selectinload` para colecciones 1-a-x/x-a-x).
- **Asincronía Pura:** Prohibido el uso de llamadas bloqueantes (`time.sleep`, `requests`). Usa `BackgroundTasks` para tareas en segundo plano.
- **Manejo de Errores:** Capturar `IntegrityError` y traducirlo a errores HTTP 409 con mensajes propios. NUNCA filtrar texto interno de la base.

## 5. Reglas de Infraestructura (Docker)

- **Imagen Base:** Obligatorio usar `python:3.12-alpine`.
- **Seguridad:** La aplicación NO debe correr como `root` (usar `USER`) y los secretos entran por variables de entorno.
- **Salud:** Configurar `HEALTHCHECK` consultando a `127.0.0.1:8000/health/ready` usando `wget`.
