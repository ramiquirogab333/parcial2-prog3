"""Lógica de negocio del módulo libros.

Reglas clave implementadas:
- RN-01: ISBN único en la base (409 con mensaje propio).
- RN-03: Precio > 0 y stock >= 0 validados en DTO y CHECK de base.
- RN-10: Paginación con limit (1 a 100, default 20) y offset (>= 0).
- RN-11: Búsqueda por título insensible a mayúsculas con parámetro ligado (ilike).
- RN-12: IntegrityError traducido a 409 sin filtrar texto interno de la base.
- Ejercicio 4: Alta de libro con relaciones (editorial_id, genero_id, autores).
  SIN if previo que verifique existencia: se escribe directamente y la base
  rechaza las claves foráneas con 409.
- Ejercicio 5: Lecturas sin N+1 con joinedload para relaciones a uno
  (editorial, género) y selectinload para la colección de autorías.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    AutorEnLibroRead,
    LibroCreate,
    LibroReadDetail,
    LibroUpdate,
)

logger = logging.getLogger(__name__)

MENSAJE_404 = "No existe un libro con ese id"


def _traducir_integrity_error(exc: IntegrityError) -> str:
    """Traduce un IntegrityError a un mensaje amigable sin exponer la base (RN-12)."""
    err_text = str(exc).lower()
    if "isbn" in err_text:
        return "Ya existe un libro con ese ISBN"
    if "editoriales" in err_text or "editorial_id" in err_text:
        return "La editorial especificada no existe"
    if "generos" in err_text or "genero_id" in err_text:
        return "El género especificado no existe"
    if "autores" in err_text or "autor_id" in err_text:
        return "Uno o más autores especificados no existen"
    if "check_libro_precio" in err_text:
        return "El precio debe ser mayor que cero"
    if "check_libro_stock" in err_text:
        return "El stock no puede ser negativo"
    if "check_libro_autor_orden" in err_text:
        return "El orden del autor debe ser mayor o igual a 1"
    if "check_libro_autor_rol" in err_text:
        return "El rol del autor no es válido"
    if "foreign key" in err_text or "violates foreign key constraint" in err_text:
        return "No se pudo registrar el libro: una o más entidades relacionadas no existen"
    return "Conflicto de integridad de datos al procesar el libro"


def a_detalle_libro(libro: Libro) -> LibroReadDetail:
    """Mapea una entidad Libro con sus relaciones cargadas a su DTO de detalle."""
    autores_dto = [
        AutorEnLibroRead(
            id=autoria.autor_id,
            autor_id=autoria.autor_id,
            nombre=autoria.autor.nombre if autoria.autor else "",
            apellido=autoria.autor.apellido if autoria.autor else "",
            nacionalidad=autoria.autor.nacionalidad if autoria.autor else None,
            rol=autoria.rol,
            orden=autoria.orden,
        )
        for autoria in sorted(libro.autorias, key=lambda a: a.orden)
    ]

    return LibroReadDetail(
        id=libro.id or 0,
        isbn=libro.isbn,
        titulo=libro.titulo,
        precio=libro.precio,
        stock=libro.stock,
        editorial_id=libro.editorial_id,
        genero_id=libro.genero_id,
        editorial=EditorialRead.model_validate(libro.editorial),
        genero=GeneroRead.model_validate(libro.genero) if libro.genero else None,
        autores=autores_dto,
    )


async def obtener_libro(session: AsyncSession, libro_id: int) -> Libro:
    """Obtiene un libro por id con todas sus relaciones precargadas (sin N+1).

    - joinedload para relaciones a uno (editorial, género, autor dentro de autoría).
    - selectinload para la colección de autorías.
    """
    stmt = (
        select(Libro)
        .where(Libro.id == libro_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )
        .execution_options(populate_existing=True)
    )
    result = await session.exec(stmt)
    libro = result.unique().one_or_none()
    if libro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return libro


async def crear_libro(session: AsyncSession, data: LibroCreate) -> LibroReadDetail:
    """Da de alta un libro con sus autores asociados.

    Cumple la consigna del Ejercicio 4:
    - Ningún `if` consulta antes si los IDs de editorial, género o autores existen.
    - Se persiste directamente; si la base rechaza una clave foránea o unicidad,
      se captura IntegrityError y se responde HTTP 409 con mensaje propio (RN-12).
    """
    libro = Libro(
        isbn=data.isbn,
        titulo=data.titulo,
        precio=data.precio,
        stock=data.stock,
        editorial_id=data.editorial_id,
        genero_id=data.genero_id,
    )

    try:
        session.add(libro)
        await session.flush()  # Genera el libro.id dentro de la transacción

        for autor_data in data.autores:
            autoria = LibroAutor(
                libro_id=libro.id,  # type: ignore[arg-type]
                autor_id=autor_data.autor_id,
                rol=autor_data.rol,
                orden=autor_data.orden,
            )
            session.add(autoria)

        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        mensaje = _traducir_integrity_error(exc)
        logger.info("Conflicto al crear libro: %s", mensaje)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje) from exc

    # Retorna el detalle con relaciones precargadas
    libro_cargado = await obtener_libro(session, libro.id)  # type: ignore[arg-type]
    return a_detalle_libro(libro_cargado)


async def listar_libros(
    session: AsyncSession,
    limit: int,
    offset: int,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> list[Libro]:
    """Lista libros paginados (RN-10) con precarga de editorial y género (sin N+1).

    - Filtro por título (RN-11): case-insensitive usando parámetro ligado (ilike).
    - Filtro por género: parámetro opcional.
    """
    stmt = (
        select(Libro)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
        .order_by(Libro.id)
        .offset(offset)
        .limit(limit)
    )

    if titulo:
        stmt = stmt.where(Libro.titulo.ilike(f"%{titulo}%"))

    if genero_id is not None:
        stmt = stmt.where(Libro.genero_id == genero_id)

    result = await session.exec(stmt)
    return list(result.unique().all())


async def actualizar_libro(
    session: AsyncSession,
    libro_id: int,
    data: LibroUpdate,
) -> LibroReadDetail:
    """Actualiza parcialmente un libro aplicando solo los campos enviados (exclude_unset)."""
    libro = await obtener_libro(session, libro_id)

    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(libro, campo, valor)

    try:
        session.add(libro)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        mensaje = _traducir_integrity_error(exc)
        logger.info("Conflicto al actualizar libro: %s", mensaje)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje) from exc

    libro_cargado = await obtener_libro(session, libro_id)
    return a_detalle_libro(libro_cargado)
