"""Carga de datos iniciales del proyecto.

Deja la base en un estado conocido para los casos de la consigna
(C-06, C-07 y D-03): editoriales, géneros, autores, libros y clientes.

Uso local:
    python -m app.seed

En el contenedor desplegado:
    docker exec libreria python -m app.seed

Es idempotente: si ya hay libros cargados, no inserta nada.
"""

import asyncio
import logging
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import async_session_factory, close_db, init_db
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor

logger = logging.getLogger(__name__)


async def cargar_datos_iniciales() -> None:
    try:
        # create_all es idempotente: solo crea las tablas que faltan.
        await init_db()

        async with async_session_factory() as session:
            resultado = await session.exec(select(func.count()).select_from(Libro))
            if resultado.one():
                print("La base ya tiene libros cargados. No se inserta nada.")
                return

            editoriales = [
                Editorial(nombre="Sudamericana", pais="Argentina"),
                Editorial(nombre="Anagrama", pais="España"),
                Editorial(nombre="Alfaguara", pais="Argentina"),
            ]
            session.add_all(editoriales)
            await session.flush()

            generos = [
                Genero(nombre="Ficción"),
                Genero(nombre="Ensayo"),
                Genero(nombre="Poesía"),
            ]
            session.add_all(generos)
            await session.flush()

            autores = [
                Autor(nombre="Julio", apellido="Cortázar", nacionalidad="Argentina"),
                Autor(nombre="Ricardo", apellido="Piglia", nacionalidad="Argentina"),
                Autor(nombre="Adolfo", apellido="Bioy Casares", nacionalidad="Argentina"),
                Autor(nombre="Silvina", apellido="Ocampo", nacionalidad="Argentina"),
            ]
            session.add_all(autores)
            await session.flush()

            libros = [
                Libro(
                    isbn="978-950-07-0001-1",
                    titulo="Rayuela",
                    precio=Decimal("25000.00"),
                    stock=10,
                    editorial_id=editoriales[0].id,
                    genero_id=generos[0].id,
                ),
                Libro(
                    isbn="978-950-00-0007-3",
                    titulo="Ficciones",
                    precio=Decimal("28500.50"),
                    stock=10,
                    editorial_id=editoriales[0].id,
                    genero_id=generos[0].id,
                ),
                Libro(
                    isbn="978-950-00-0006-6",
                    titulo="Los que aman, odian",
                    precio=Decimal("21000.00"),
                    stock=4,
                    editorial_id=editoriales[0].id,
                    genero_id=generos[0].id,
                ),
                Libro(
                    isbn="978-950-07-0002-8",
                    titulo="Respiración artificial",
                    precio=Decimal("27000.00"),
                    stock=5,
                    editorial_id=editoriales[1].id,
                    genero_id=generos[1].id,
                ),
            ]
            session.add_all(libros)
            await session.flush()

            # Autorías (rol y orden son datos de la relación, no del libro ni del autor).
            session.add_all(
                [
                    LibroAutor(libro_id=libros[0].id, autor_id=autores[0].id, rol="autor", orden=1),
                    LibroAutor(libro_id=libros[1].id, autor_id=autores[2].id, rol="autor", orden=1),
                    LibroAutor(libro_id=libros[1].id, autor_id=autores[3].id, rol="coautor", orden=2),
                    LibroAutor(libro_id=libros[2].id, autor_id=autores[2].id, rol="coautor", orden=1),
                    LibroAutor(libro_id=libros[2].id, autor_id=autores[3].id, rol="coautor", orden=2),
                    LibroAutor(libro_id=libros[3].id, autor_id=autores[1].id, rol="autor", orden=1),
                ]
            )

            clientes = [
                Cliente(nombre="Ana Pérez", email="ana@example.com"),
                Cliente(nombre="Tomás Ríos", email="tomas@example.com"),
            ]
            session.add_all(clientes)
            await session.flush()

            session.add(
                PerfilCliente(
                    cliente_id=clientes[0].id,
                    telefono="2614440000",
                    direccion="Belgrano 456",
                )
            )

            await session.commit()

            resumen = {
                "editoriales": [(e.id, e.nombre) for e in editoriales],
                "generos": [(g.id, g.nombre) for g in generos],
                "autores": [(a.id, f"{a.nombre} {a.apellido}") for a in autores],
                "libros": [(libro.id, libro.titulo) for libro in libros],
                "clientes": [(c.id, c.nombre) for c in clientes],
            }

        print("Datos iniciales cargados:")
        for clave, valores in resumen.items():
            print(f"  {clave}: {valores}")
    finally:
        await close_db()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(cargar_datos_iniciales())


if __name__ == "__main__":
    main()
