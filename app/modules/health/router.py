from fastapi import APIRouter, Depends, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.health import service
from app.modules.health.schemas import LiveResponse, ReadyResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    """Liveness: el proceso está vivo y atiende requests. No toca la base."""
    return LiveResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
)
async def ready(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> ReadyResponse:
    """Readiness: la API puede atender porque PostgreSQL responde.

    Devuelve 200 si la base está arriba y 503 si no (lo usa el HEALTHCHECK de Docker).
    """
    if await service.database_is_up(session):
        return ReadyResponse(status="ok", database="up")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="error", database="down")
