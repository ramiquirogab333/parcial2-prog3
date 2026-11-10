# CHANGE.md - Roadmap Secuencial y Asignación de Turnos

## Metodología de Trabajo (Cascada Estricta)
El equipo trabajará sobre una única rama (`main`). Nadie comienza a escribir código hasta que el integrante del turno anterior haya realizado el `push` final y notificado al equipo de que su módulo está funcional. El archivo `AGENTS.md` se mantiene idéntico, ya que las reglas arquitectónicas para la IA no cambian.

1. **Turno 1:** Configuración inicial, motor asincrónico y módulo Health.
2. **Turno 2:** CRUDs independientes (Editoriales y Géneros).
3. **Turno 3:** CRUDs de Autores y Clientes (con relación 1 a 1).
4. **Turno 4:** Módulo Libros (ensamblando relaciones simples y N:M).
5. **Turno 5:** Módulo Ventas (composición, cálculos y asincronía).
6. **Turno 6:** Dockerización, VPS y despliegue final (Aislado).

---

## Asignación de Tareas por Turno

### Turno 1: Core y Base de Datos (Emmanuel)
* **Responsabilidad:** Setup inicial de la arquitectura FastAPI y SQLModel para que el resto pueda construir encima[cite: 1, 3].
* **Tareas:**
    * Crear `app/main.py` con el `lifespan` para inicializar la conexión a PostgreSQL e invocar `create_all`[cite: 7].
    * Configurar `database.py` con la dependencia `get_session` y el motor `asyncpg`[cite: 6, 7].
    * Implementar el módulo `health` para las comprobaciones de estado (`GET /health/live` y `GET /health/ready`)[cite: 7].

### Turno 2: Entidades de Agregación (Santiago)
* **Responsabilidad:** Construir los catálogos base estáticos que requerirá el libro más adelante[cite: 2].
* **Tareas:**
    * Desarrollar por completo los módulos `editoriales` y `generos` (Modelos, Schemas, Service, Router)[cite: 6].
    * Asegurar la validación de unicidad en los nombres dentro de la base de datos, gestionando correctamente la respuesta HTTP 409[cite: 4, 11].
    * Crear los primeros casos de prueba en archivos `.http` dentro de la carpeta `test/`[cite: 6].

### Turno 3: Autores y Clientes (Ignacio)
* **Responsabilidad:** Entidades secundarias complejas y la relación 1 a 1 del modelo de negocio[cite: 2].
* **Tareas:**
    * Desarrollar el módulo `autores` (alta, edición y obtención de detalle)[cite: 6, 12].
    * Desarrollar el módulo `clientes`, implementando tanto el modelo `Cliente` como `PerfilCliente`[cite: 4].
    * Garantizar por base de datos (UNIQUE) que el cliente tenga como máximo un solo perfil (Regla RN-09) y manejar el error 409 si se intenta duplicar un email (Regla RN-02)[cite: 5].

### Turno 4: Entidad Central y Relaciones Múltiples (Ciro)
* **Responsabilidad:** Consolidar el catálogo uniendo todo el trabajo de los turnos 2 y 3[cite: 2, 4].
* **Tareas:**
    * Crear el módulo `libros` y modelar la clase intermedia `LibroAutor` con sus atributos específicos (`rol` y `orden`)[cite: 4].
    * Desarrollar el alta (`POST /libros/`) recibiendo en el cuerpo los IDs de editoriales/géneros y la lista de autores completa[cite: 7, 13].
    * Implementar las lecturas garantizando que no ocurra el problema N+1, paginando los listados y permitiendo la búsqueda por título con parámetros ligados (Reglas RN-10 y RN-11)[cite: 5, 8].

### Turno 5: Lógica Transaccional (Ramiro)
* **Responsabilidad:** Último módulo de código funcional, centrado en cálculos y operaciones asincrónicas[cite: 1, 2].
* **Tareas:**
    * Construir el módulo `ventas`, incluyendo la lógica de composición entre `Venta` y `RenglonVenta`[cite: 4].
    * Desarrollar la creación de ventas (`POST /ventas/`) cumpliendo estrictamente las reglas RN-04 a RN-07: el servidor debe calcular el total copiando el precio actual del libro y usar tipado `Decimal`[cite: 5, 12].
    * Implementar el uso de `BackgroundTasks` para simular el aviso del comprobante (con `asyncio.sleep`) garantizando la ejecución asincrónica sin bloqueos[cite: 8].

### Turno 6: Docker, Infraestructura y Despliegue VPS (Franco)
* **Responsabilidad:** Exclusivamente el empaquetado del software, la gestión de contenedores y la puesta en marcha en el servidor de la cátedra[cite: 1, 9]. (No desarrolla endpoints, asume el código de la Fase 5 como final).
* **Tareas:**
    * Escribir el `Dockerfile` partiendo obligatoriamente de la imagen `python:3.12-alpine` para respetar el límite de peso[cite: 9].
    * Configurar un usuario sin privilegios para ejecutar la aplicación (USER) y declarar el `HEALTHCHECK` consultando a `127.0.0.1:8000/health/ready` (ya que `localhost` da problemas de IPv6 en Alpine)[cite: 9, 10].
    * Asegurar que los secretos (como el archivo `.env`) no se horneen en la imagen mediante el uso de `.dockerignore`[cite: 9].
    * Ejecutar el despliegue en el VPS asignando el puerto indicado (`-p <puerto>:8000`) y pasándole las variables de entorno externamente con `--env-file`[cite: 10].
    * Entrar al contenedor en el servidor (`docker exec`) para ejecutar los scripts de carga de datos iniciales en PostgreSQL[cite: 11].
    * Redactar el documento final `DEPLOY.md` detallando los comandos utilizados, la URL pública y documentando las salidas de diagnóstico requeridas para la entrega[cite: 11, 16].