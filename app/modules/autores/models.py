"""Modelo de tabla del módulo autores."""

from sqlmodel import Field, SQLModel


class Autor(SQLModel, table=True):
    __tablename__ = "autores"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=80)
    apellido: str = Field(max_length=80)
    nacionalidad: str | None = Field(default=None, max_length=60)

    # TODO(Turno 4 - Libros): la relación N:M con Libro se modela con la clase
    # intermedia LibroAutor (rol, orden). Lo implementa el turno de Libros.
