"""Modelo de tabla del módulo generos."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Genero(SQLModel, table=True):
    __tablename__ = "generos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=80)

    # Relación 1 a x con Libro (agregación opcional en Libro)
    libros: list["Libro"] = Relationship(back_populates="genero")

