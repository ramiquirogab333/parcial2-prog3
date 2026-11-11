# Evidencia — Parcial Cap. 1 a 4 (Grupo 11)

Despliegue público: **https://libros.francogagliardi.me**

| Caso | Archivo | Resultado |
| --- | --- | --- |
| C-07 | `C-07_consultas.txt` | 2 SELECT fijas para un libro con 1 autor, con 2 autores y para una venta con 2 renglones |
| D-01 | `D-01_docker_images.txt` | `python:3.12-alpine` 74.8 MB; imagen del proyecto 209 MB |
| D-02 | `D-02_contenedor_healthy.txt` y `D-02_build_log.txt` | Build con Dockerfile, contenedor `healthy` y arranque con las tablas creadas |
| D-03 | `D-03_url_publica.txt` | `/health/ready` 200, `/libros/` 200 y `POST /ventas/` 201 |
| D-04 | `D-04_recreacion.txt` | Se elimina la tarea y Swarm la recrea `healthy`; los libros y la venta siguen |
| D-05 | `D-05_sin_database_url.txt` | Sin `DATABASE_URL` el contenedor termina con `exit=1` |
| D-06 | `D-06_usuario.txt` | `uid=10001(appuser)`, no root |
| D-07 | `D-07_comprobante.txt` | El aviso del comprobante aparece 0.5 s después de la respuesta 201 |

## Notas

- El despliegue en línea se hace con **Easypanel** (Docker Swarm). La imagen se construye
  con el `Dockerfile` del proyecto y se ejecuta como App service `grupo_11/libreria-api`.
- D-03 se tomó desde afuera del VPS, sobre la URL pública con HTTPS.
- D-04 se hizo sobre el servicio de Swarm: se elimina la tarea y Swarm crea una nueva;
  los datos persisten en el servicio PostgreSQL.
- D-05 usa `docker run` directamente sobre la imagen, sin `DATABASE_URL`.
- C-07 se tomó con la misma imagen y `SQL_ECHO=true`; el detalle muestra una cantidad
  fija de consultas, sin N+1.
