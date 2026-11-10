"""Lógica de negocio de clientes.

- RN-02: el email es UNIQUE en la base. Sin SELECT previo: se intenta el commit
  y `IntegrityError` se traduce a 409 con mensaje propio.
- RN-09: `perfiles_cliente.cliente_id` es UNIQUE, así que la base impide un
  segundo perfil para el mismo cliente (también se traduce a 409).
- Toda lectura trae el perfil con `joinedload` en la misma consulta (sin N+1).
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    PerfilClienteCreate,
)

logger = logging.getLogger(__name__)

MENSAJE_404 = "No existe un cliente con ese id"
MENSAJE_409_EMAIL = "Ya existe un cliente con ese email"
MENSAJE_409_PERFIL = "El cliente ya tiene un perfil"


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    """Devuelve el cliente con su perfil cargado en la misma consulta."""
    stmt = (
        select(Cliente)
        .where(Cliente.id == cliente_id)
        .options(joinedload(Cliente.perfil))
        .execution_options(populate_existing=True)
    )
    cliente = (await session.exec(stmt)).unique().one_or_none()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return cliente


async def listar_clientes(session: AsyncSession, limit: int, offset: int) -> list[Cliente]:
    stmt = (
        select(Cliente)
        .options(joinedload(Cliente.perfil))
        .order_by(Cliente.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.exec(stmt)
    return list(result.unique().all())


async def crear_cliente(session: AsyncSession, data: ClienteCreate) -> Cliente:
    cliente = Cliente(nombre=data.nombre, email=data.email)
    try:
        session.add(cliente)
        await session.flush()  # obtiene el id sin cerrar la transacción
        if data.perfil is not None:
            session.add(PerfilCliente(cliente_id=cliente.id, **data.perfil.model_dump()))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al crear cliente: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409_EMAIL) from exc
    return await obtener_cliente(session, cliente.id)


async def actualizar_cliente(
    session: AsyncSession, cliente_id: int, data: ClienteUpdate
) -> Cliente:
    cliente = await obtener_cliente(session, cliente_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    try:
        session.add(cliente)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al actualizar cliente: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409_EMAIL) from exc
    return await obtener_cliente(session, cliente_id)


async def crear_perfil(
    session: AsyncSession, cliente_id: int, data: PerfilClienteCreate
) -> Cliente:
    await obtener_cliente(session, cliente_id)  # 404 si no existe
    try:
        session.add(PerfilCliente(cliente_id=cliente_id, **data.model_dump()))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.info("Conflicto al crear perfil: %s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_409_PERFIL) from exc
    return await obtener_cliente(session, cliente_id)
