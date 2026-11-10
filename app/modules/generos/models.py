"""Modelo de tabla del módulo generos."""

from sqlmodel import Field, SQLModel


class Genero(SQLModel, table=True):
    __tablename__ = "generos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=80)

    # TODO(Turno 4 - Libros): agregar la relación N:M con Libro (tabla intermedia)
    # y el endpoint GET /generos/{id}/libros. Lo implementa el turno de Libros.
