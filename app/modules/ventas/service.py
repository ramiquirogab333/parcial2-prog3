"""Lógica de negocio del módulo ventas.

Reglas clave implementadas:
- RN-04: la venta se crea con sus renglones (se agregan a venta.renglones).
- RN-05: al menos un renglón y sin libros repetidos (validado en el DTO, 422).
- RN-06: el precio unitario se copia del libro leyéndolo de la base.
- RN-07: el total lo calcula el servidor (suma de cantidad * precio unitario).
- RN-08: no hay actualización de ventas.
- Stock: cada venta descuenta del libro la cantidad vendida (409 si no alcanza).
- RN-10: listados paginados con limit/offset.
- RN-12: IntegrityError traducido a 409 sin filtrar texto interno de la base.
- Ejercicio 5: lecturas sin N+1 (joinedload para cliente y libro,
  selectinload para la colección de renglones).
- Ejercicio 6: aviso del comprobante asincrónico (asyncio.sleep) vía BackgroundTasks.
"""

import asyncio
import logging
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.clientes.models import Cliente
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import (
    ClienteEnVentaRead,
    RenglonVentaRead,
    VentaCreate,
    VentaReadDetail,
    VentaReadList,
)

logger = logging.getLogger(__name__)

MENSAJE_404 = "No existe una venta con ese id"
MENSAJE_404_CLIENTE = "No existe un cliente con ese id"
MENSAJE_LIBRO_INEXISTENTE = "Uno o más libros especificados no existen"
CENTAVOS = Decimal("0.01")


def _traducir_integrity_error(exc: IntegrityError) -> str:
    """Traduce un IntegrityError a un mensaje propio sin exponer la base (RN-12)."""
    # Solo el mensaje de PostgreSQL (exc.orig): str(exc) incluye el SQL del INSERT.
    err_text = str(exc.orig).lower()
    if "cliente_id" in err_text:
        return "El cliente especificado no existe"
    if "libro_id" in err_text:
        return MENSAJE_LIBRO_INEXISTENTE
    if "check_libro_stock" in err_text:
        return "No hay stock suficiente para completar la venta"
    if "check_renglon_cantidad" in err_text:
        return "La cantidad de cada renglón debe ser mayor que cero"
    if "check_renglon_precio" in err_text:
        return "El precio unitario debe ser mayor que cero"
    if "check_venta_total" in err_text:
        return "El total de la venta no puede ser negativo"
    return "Conflicto de integridad de datos al registrar la venta"


def calcular_total(renglones: list[RenglonVenta]) -> Decimal:
    """RN-07: suma de cantidad * precio unitario, redondeada a centavos."""
    total = sum((r.precio_unitario * r.cantidad for r in renglones), Decimal("0"))
    return total.quantize(CENTAVOS)


def a_lista_venta(venta: Venta) -> VentaReadList:
    return VentaReadList(
        id=venta.id or 0,
        fecha=venta.fecha,
        total=venta.total,
        cliente=ClienteEnVentaRead.model_validate(venta.cliente),
    )


def a_detalle_venta(venta: Venta) -> VentaReadDetail:
    """Mapea una Venta con cliente y renglones (y su libro) cargados a su DTO de detalle."""
    renglones = [
        RenglonVentaRead(
            libro_id=r.libro_id,
            titulo=r.libro.titulo if r.libro else "",
            cantidad=r.cantidad,
            precio_unitario=r.precio_unitario,
            subtotal=(r.precio_unitario * r.cantidad).quantize(CENTAVOS),
        )
        for r in sorted(venta.renglones, key=lambda r: r.id or 0)
    ]
    return VentaReadDetail(
        id=venta.id or 0,
        fecha=venta.fecha,
        total=venta.total,
        cliente=ClienteEnVentaRead.model_validate(venta.cliente),
        renglones=renglones,
    )


async def obtener_venta(session: AsyncSession, venta_id: int) -> Venta:
    """Obtiene una venta con cliente y renglones precargados (cantidad fija de consultas)."""
    stmt = (
        select(Venta)
        .where(Venta.id == venta_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .execution_options(populate_existing=True)
    )
    result = await session.exec(stmt)
    venta = result.unique().one_or_none()
    if venta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404)
    return venta


async def crear_venta(session: AsyncSession, data: VentaCreate) -> VentaReadDetail:
    """Registra una venta con sus renglones (RN-04 a RN-07) y descuenta el stock.

    - Los libros se leen en UNA consulta con SELECT ... FOR UPDATE: las filas
      quedan bloqueadas hasta el commit, así dos ventas simultáneas no pueden
      vender el mismo ejemplar (el CHECK stock >= 0 es la última barrera).
    - El precio de cada libro se copia al renglón (RN-06).
    - Libro inexistente o stock insuficiente => 409 con mensaje propio.
    - El cliente no se consulta antes: si no existe, la base rechaza la clave
      foránea y se responde 409 (RN-12).
    """
    libro_ids = [r.libro_id for r in data.renglones]
    result = await session.exec(
        select(Libro).where(Libro.id.in_(libro_ids)).order_by(Libro.id).with_for_update()
    )
    libros: dict[int, Libro] = {libro.id: libro for libro in result.all()}  # type: ignore[misc]

    if len(libros) != len(set(libro_ids)):
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAJE_LIBRO_INEXISTENTE)

    for renglon_data in data.renglones:
        libro = libros[renglon_data.libro_id]
        if libro.stock < renglon_data.cantidad:
            # El mensaje se arma ANTES del rollback: el rollback vence los
            # atributos cargados y leerlos después dispararía una carga implícita.
            mensaje = f"Stock insuficiente para el libro '{libro.titulo}' (disponible: {libro.stock})"
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje)

    venta = Venta(cliente_id=data.cliente_id)
    for renglon_data in data.renglones:
        libro = libros[renglon_data.libro_id]
        libro.stock -= renglon_data.cantidad
        venta.renglones.append(
            RenglonVenta(
                libro_id=renglon_data.libro_id,
                cantidad=renglon_data.cantidad,
                precio_unitario=libro.precio,
            )
        )
    venta.total = calcular_total(venta.renglones)

    try:
        session.add(venta)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        mensaje = _traducir_integrity_error(exc)
        logger.info("Conflicto al crear venta: %s", mensaje)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje) from exc

    venta_cargada = await obtener_venta(session, venta.id)  # type: ignore[arg-type]
    return a_detalle_venta(venta_cargada)


async def listar_ventas(
    session: AsyncSession,
    limit: int,
    offset: int,
    cliente_id: int | None = None,
) -> list[VentaReadList]:
    """Lista ventas paginadas (RN-10) con el cliente precargado (sin N+1)."""
    stmt = (
        select(Venta)
        .options(joinedload(Venta.cliente))
        .order_by(Venta.id)
        .offset(offset)
        .limit(limit)
    )
    if cliente_id is not None:
        stmt = stmt.where(Venta.cliente_id == cliente_id)

    result = await session.exec(stmt)
    return [a_lista_venta(v) for v in result.unique().all()]


async def listar_ventas_de_cliente(
    session: AsyncSession, cliente_id: int, limit: int, offset: int
) -> list[VentaReadList]:
    """Ventas de un cliente. 404 si el cliente no existe."""
    if await session.get(Cliente, cliente_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_404_CLIENTE)
    return await listar_ventas(session, limit=limit, offset=offset, cliente_id=cliente_id)


async def enviar_comprobante(venta_id: int, email: str, total: Decimal) -> None:
    """Simula el aviso del comprobante al cliente sin bloquear el event loop (Ejercicio 6)."""
    await asyncio.sleep(0.5)
    logger.info("Comprobante de la venta %s enviado a %s (total %s)", venta_id, email, total)
