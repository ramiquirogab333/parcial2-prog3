from typing import Literal

from sqlmodel import SQLModel


class LiveResponse(SQLModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(SQLModel):
    status: Literal["ok", "error"]
    database: Literal["up", "down"]
