"""Lógica de negocio de autores."""

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorUpdate

MENSAJE_404 = "No existe un autor con ese id"


async def crear_autor(session: AsyncSession, data: AutorCreate) -> Autor:
    autor = Autor.model_validate(data)
    session.add(autor)
    await session.commit()
    await session.refresh(autor)
    return autor


async def listar_autores(session: AsyncSession, limit: int, offset: int) -> list[Autor]:
    result = await session.exec(select(Autor).order_by(Autor.id).offset(offset).limit(limit))
    return list(result.all())


async def obtener_autor(session: AsyncSession, autor_id: int) -> Autor:
    autor = await session.get(Autor, autor_id)
    if autor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return autor


async def actualizar_autor(session: AsyncSession, autor_id: int, data: AutorUpdate) -> Autor:
    autor = await obtener_autor(session, autor_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(autor, campo, valor)
    session.add(autor)
    await session.commit()
    await session.refresh(autor)
    return autor
