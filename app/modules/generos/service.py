"""Lógica de negocio de generos.

La unicidad de `nombre` la garantiza PostgreSQL (UNIQUE). Sin SELECT previo:
se intenta el commit y se traduce `IntegrityError` a un 409 con mensaje propio.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate
from app.modules.libros.models import Libro

logger = logging.getLogger(__name__)

MENSAJE_409 = "Ya existe un género con ese nombre"
MENSAJE_404 = "No existe un género con ese id"


async def crear_genero(session: AsyncSession, data: GeneroCreate) -> Genero:
    genero = Genero.model_validate(data)
    try:
        session.add(genero)
        await session.commit()
        await session.refresh(genero)
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al crear género: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409) from exc
    return genero


async def listar_generos(session: AsyncSession) -> list[Genero]:
    result = await session.exec(select(Genero))
    return list(result.all())


async def obtener_genero(session: AsyncSession, genero_id: int) -> Genero:
    """Devuelve un género por su id o 404 si no existe."""
    genero = await session.get(Genero, genero_id)
    if genero is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return genero


async def listar_libros_por_genero(
    session: AsyncSession, genero_id: int
) -> list[Libro]:
    """Lista todos los libros clasificados en un género con precarga de editorial y género."""
    await obtener_genero(session, genero_id)  # 404 si el género no existe
    stmt = (
        select(Libro)
        .where(Libro.genero_id == genero_id)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
        )
        .order_by(Libro.id)
    )
    result = await session.exec(stmt)
    return list(result.unique().all())
