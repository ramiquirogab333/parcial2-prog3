"""Modelos de tabla del módulo clientes: Cliente y PerfilCliente (relación 1 a 1)."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    __tablename__ = "clientes"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=120)
    # RN-02: el email es único, lo garantiza PostgreSQL.
    email: str = Field(unique=True, index=True, max_length=254)

    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False},
    )
    # Asociación con Venta (Turno 5): navegación en los dos extremos.
    ventas: list["Venta"] = Relationship(back_populates="cliente")


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfiles_cliente"

    id: int | None = Field(default=None, primary_key=True)
    # RN-09: UNIQUE en la FK => un cliente tiene como máximo un perfil.
    cliente_id: int = Field(foreign_key="clientes.id", unique=True, index=True)
    telefono: str | None = Field(default=None, max_length=30)
    direccion: str | None = Field(default=None, max_length=200)

    cliente: Optional[Cliente] = Relationship(back_populates="perfil")
