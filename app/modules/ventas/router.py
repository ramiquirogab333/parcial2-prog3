"""Router HTTP del módulo ventas.

No hay PATCH ni DELETE: las ventas registran un hecho (RN-08).
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaReadDetail, VentaReadList

router = APIRouter(tags=["Ventas"])

R404 = {status.HTTP_404_NOT_FOUND: {"description": "No existe una venta con ese id"}}
R404_CLIENTE = {status.HTTP_404_NOT_FOUND: {"description": "No existe un cliente con ese id"}}
R409 = {status.HTTP_409_CONFLICT: {"description": "Cliente o libro inexistente"}}


@router.post(
    "/ventas/",
    response_model=VentaReadDetail,
    status_code=status.HTTP_201_CREATED,
    responses=R409,
)
async def crear_venta(
    data: VentaCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> VentaReadDetail:
    """Registra una venta con sus renglones; precios copiados y total calculado por el servidor.

    El aviso del comprobante se agenda con BackgroundTasks y corre después de
    enviar la respuesta.
    """
    venta = await service.crear_venta(session, data)
    background_tasks.add_task(
        service.enviar_comprobante, venta.id, venta.cliente.email, venta.total
    )
    return venta


@router.get("/ventas/", response_model=list[VentaReadList])
async def listar_ventas(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
) -> list[VentaReadList]:
    """Lista ventas con su cliente, paginadas por limit/offset (RN-10)."""
    return await service.listar_ventas(session, limit=limit, offset=offset)


@router.get("/ventas/{venta_id}", response_model=VentaReadDetail, responses=R404)
async def obtener_venta(
    venta_id: int,
    session: AsyncSession = Depends(get_session),
) -> VentaReadDetail:
    """Detalle de la venta con cliente y renglones (cantidad fija de consultas)."""
    venta = await service.obtener_venta(session, venta_id)
    return service.a_detalle_venta(venta)


@router.get(
    "/clientes/{cliente_id}/ventas",
    response_model=list[VentaReadList],
    responses=R404_CLIENTE,
)
async def listar_ventas_de_cliente(
    cliente_id: int,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
) -> list[VentaReadList]:
    """Ventas de un cliente, paginadas (RN-10)."""
    return await service.listar_ventas_de_cliente(
        session, cliente_id, limit=limit, offset=offset
    )
