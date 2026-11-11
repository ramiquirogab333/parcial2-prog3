from typing import Literal

from sqlmodel import SQLModel


class LiveResponse(SQLModel):
    # La tabla de endpoints de la consigna espera {"estado": "vivo"}.
    estado: Literal["vivo"] = "vivo"


class ReadyResponse(SQLModel):
    status: Literal["ok", "error"]
    database: Literal["up", "down"]
