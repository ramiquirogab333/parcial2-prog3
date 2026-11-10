"""Lógica de negocio de generos.

La unicidad de `nombre` la garantiza PostgreSQL (UNIQUE). Sin SELECT previo:
se intenta el commit y se traduce `IntegrityError` a un 409 con mensaje propio.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate

logger = logging.getLogger(__name__)

MENSAJE_409 = "Ya existe un género con ese nombre"


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
