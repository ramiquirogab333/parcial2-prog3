"""DTOs de ventas (contratos de entrada/salida, separados de los modelos de tabla).

RN-06 y RN-07: ni el precio unitario, ni el total, ni la fecha viajan en el DTO
de entrada; los resuelve el servidor.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator
from sqlmodel import SQLModel

# --- Entrada (Create). No hay Update: las ventas no se modifican (RN-08). ---


class RenglonVentaCreate(SQLModel):
    """Datos de un renglón dentro del alta de la venta (composición, RN-04)."""

    libro_id: int = Field(gt=0, description="Id de un libro existente")
    cantidad: int = Field(gt=0, description="Cantidad de ejemplares (> 0)")


class VentaCreate(SQLModel):
    """Cuerpo del POST /ventas/: viaja el id del cliente y los renglones."""

    cliente_id: int = Field(gt=0, description="Id de un cliente existente")
    # RN-05: al menos un renglón.
    renglones: list[RenglonVentaCreate] = Field(
        min_length=1, description="Renglones de la venta (al menos uno)"
    )

    @field_validator("renglones")
    @classmethod
    def sin_libros_repetidos(cls, renglones: list[RenglonVentaCreate]) -> list[RenglonVentaCreate]:
        """RN-05: un mismo libro no aparece en dos renglones (422)."""
        ids = [r.libro_id for r in renglones]
        if len(ids) != len(set(ids)):
            raise ValueError("Un mismo libro no puede aparecer en dos renglones")
        return renglones


# --- Salida (Read) ---


class ClienteEnVentaRead(SQLModel):
    id: int
    nombre: str
    email: str


class RenglonVentaRead(SQLModel):
    libro_id: int
    titulo: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaReadList(SQLModel):
    """Venta en listados: con su cliente, sin renglones."""

    id: int
    fecha: datetime
    total: Decimal
    cliente: ClienteEnVentaRead


class VentaReadDetail(VentaReadList):
    """Detalle de una venta: cliente y renglones con precio copiado y subtotal."""

    renglones: list[RenglonVentaRead] = Field(default_factory=list)
