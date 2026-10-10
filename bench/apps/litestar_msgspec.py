"""Litestar + msgspec Structs + asyncpg."""

import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

import msgspec
from litestar import Litestar, get, post

from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, close_pool, get_pool, open_pool, random_id

class Message(msgspec.Struct):
    message: str


class Item(msgspec.Struct):
    id: int
    name: str
    price: float
    quantity: int
    tags: list[str]
    created_at: datetime


class ItemIn(msgspec.Struct):
    name: Annotated[str, msgspec.Meta(min_length=1, max_length=100)]
    price: Annotated[float, msgspec.Meta(gt=0)]
    quantity: Annotated[int, msgspec.Meta(ge=0)]
    tags: list[str] = []


@get("/json")
async def json_endpoint() -> Message:
    return Message(message="Hello, World!")


@get("/db")
async def single_query() -> Item:
    async with get_pool().acquire() as conn:
        return Item(**await conn.fetchrow(SQL_ONE, random_id()))


@get("/queries")
async def multiple_queries(n: int = 20) -> list[Item]:
    async with get_pool().acquire() as conn:
        return [Item(**await conn.fetchrow(SQL_ONE, random_id())) for _ in range(clamp(n))]


@get("/items")
async def list_items(limit: int = 100) -> list[Item]:
    async with get_pool().acquire() as conn:
        return [Item(**r) for r in await conn.fetch(SQL_MANY, clamp(limit))]


@post("/items")
async def create_item(data: ItemIn) -> Item:
    async with get_pool().acquire() as conn:
        return Item(**await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags))


@asynccontextmanager
async def lifespan(_: Litestar):
    await open_pool()
    print(f"[litestar-msgspec] GIL enabled: {sys._is_gil_enabled()}", flush=True)
    yield
    await close_pool()


app = Litestar(
    route_handlers=[json_endpoint, single_query, multiple_queries, list_items, create_item],
    lifespan=[lifespan],
    openapi_config=None,
)
