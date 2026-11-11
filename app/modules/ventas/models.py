"""Modelos de tabla del módulo ventas: Venta y RenglonVenta (composición)."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import Libro


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Venta(SQLModel, table=True):
    """Venta registrada (hecho inmutable, RN-08: no hay PATCH)."""

    __tablename__ = "venta"
    __table_args__ = (CheckConstraint("total >= 0", name="check_venta_total_no_negativo"),)

    id: int | None = Field(default=None, primary_key=True)
    # Asociación: la venta conoce al cliente, pero ninguno es parte del otro.
    cliente_id: int = Field(foreign_key="cliente.id", index=True)
    # Fecha con zona horaria (TIMESTAMP WITH TIME ZONE).
    fecha: datetime = Field(
        default_factory=_ahora_utc,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # RN-07: lo calcula el servidor. Dinero con Decimal / NUMERIC(12, 2).
    total: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False),
    )

    cliente: Optional["Cliente"] = Relationship(back_populates="ventas")
    # Composición: los renglones nacen y mueren con su venta.
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RenglonVenta(SQLModel, table=True):
    """Renglón de una venta: qué libro, cuántos ejemplares y a qué precio."""

    __tablename__ = "renglon_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_renglon_cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="check_renglon_precio_positivo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id", index=True)
    # Asociación: el renglón nombra un libro que ya existe.
    libro_id: int = Field(foreign_key="libro.id", index=True)
    cantidad: int = Field()
    # RN-06: copiado del libro al registrar la venta; no cambia después.
    precio_unitario: Decimal = Field(
        sa_column=Column(Numeric(precision=10, scale=2), nullable=False)
    )

    venta: Optional[Venta] = Relationship(back_populates="renglones")
    libro: Optional["Libro"] = Relationship(back_populates="renglones")
