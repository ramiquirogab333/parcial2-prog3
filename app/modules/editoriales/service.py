"""Lógica de negocio de editoriales.

La unicidad de `nombre` la garantiza PostgreSQL (UNIQUE). Acá NO se hace un
SELECT previo para verificar duplicados: se intenta el commit y, si la base
rechaza la operación, se traduce `IntegrityError` a un 409 con mensaje propio
(sin filtrar texto interno de la base).
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate
from app.modules.libros.models import Libro

logger = logging.getLogger(__name__)

MENSAJE_409 = "Ya existe una editorial con ese nombre"
MENSAJE_404 = "No existe una editorial con ese id"


async def crear_editorial(session: AsyncSession, data: EditorialCreate) -> Editorial:
    editorial = Editorial.model_validate(data)
    try:
        session.add(editorial)
        await session.commit()
        await session.refresh(editorial)
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al crear editorial: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409) from exc
    return editorial


async def listar_editoriales(
    session: AsyncSession, limit: int, offset: int
) -> list[Editorial]:
    result = await session.exec(select(Editorial).offset(offset).limit(limit))
    return list(result.all())


async def obtener_editorial(session: AsyncSession, editorial_id: int) -> Editorial:
    editorial = await session.get(Editorial, editorial_id)
    if editorial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return editorial


async def actualizar_editorial(
    session: AsyncSession, editorial_id: int, data: EditorialUpdate
) -> Editorial:
    editorial = await obtener_editorial(session, editorial_id)
    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(editorial, campo, valor)
    try:
        session.add(editorial)
        await session.commit()
        await session.refresh(editorial)
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al actualizar editorial: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409) from exc
    return editorial


async def listar_libros_por_editorial(
    session: AsyncSession, editorial_id: int
) -> list[Libro]:
    """Lista todos los libros publicados por una editorial con precarga de editorial y género."""
    await obtener_editorial(session, editorial_id)  # 404 si la editorial no existe
    stmt = (
        select(Libro)
        .where(Libro.editorial_id == editorial_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
        .order_by(Libro.id)
    )
    result = await session.exec(stmt)
    return list(result.unique().all())
