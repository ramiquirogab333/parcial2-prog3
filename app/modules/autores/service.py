"""Lógica de negocio de autores."""

from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorUpdate
from app.modules.libros.models import LibroAutor
from app.modules.libros.schemas import LibroEnAutorRead

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


async def listar_libros_por_autor(
    session: AsyncSession, autor_id: int
) -> list[LibroEnAutorRead]:
    """Lista todos los libros asociados a un autor, con el rol y el orden de la autoría."""
    await obtener_autor(session, autor_id)  # 404 si el autor no existe
    stmt = (
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.orden)
    )
    result = await session.exec(stmt)
    autorias = result.all()
    return [
        LibroEnAutorRead(
            id=a.libro.id or 0,
            libro_id=a.libro.id or 0,
            isbn=a.libro.isbn,
            titulo=a.libro.titulo,
            precio=a.libro.precio,
            stock=a.libro.stock,
            editorial_id=a.libro.editorial_id,
            genero_id=a.libro.genero_id,
            rol=a.rol,
            orden=a.orden,
        )
        for a in autorias
        if a.libro is not None
    ]
