"""Shared pieces for the FastAPI variants (pool lifespan + pydantic models)."""

import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from common import close_pool, open_pool


class Message(BaseModel):
    message: str


class Item(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    tags: list[str]
    created_at: datetime


class ItemIn(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    price: Annotated[float, Field(gt=0)]
    quantity: Annotated[int, Field(ge=0)]
    tags: list[str] = []


def make_lifespan(label: str):
    @asynccontextmanager
    async def lifespan(_):
        await open_pool()
        print(f"[{label}] GIL enabled: {sys._is_gil_enabled()}", flush=True)
        yield
        await close_pool()

    return lifespan


def row_to_dict(r) -> dict:
    """Plain-JSON-safe dict for the stdlib json / ujson variants."""
    d = dict(r)
    d["created_at"] = d["created_at"].isoformat()
    return d
