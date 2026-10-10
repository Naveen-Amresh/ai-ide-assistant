"""FastAPI + pydantic v2 (response_model serialization via pydantic-core) + asyncpg."""

from fastapi import FastAPI

from apps._fastapi_base import Item, ItemIn, Message, make_lifespan
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, get_pool, random_id

app = FastAPI(lifespan=make_lifespan("fastapi-pydantic"), openapi_url=None, docs_url=None, redoc_url=None)


@app.get("/json")
async def json_endpoint() -> Message:
    return Message(message="Hello, World!")


@app.get("/db")
async def single_query() -> Item:
    async with get_pool().acquire() as conn:
        return dict(await conn.fetchrow(SQL_ONE, random_id()))


@app.get("/queries")
async def multiple_queries(n: int = 20) -> list[Item]:
    async with get_pool().acquire() as conn:
        return [dict(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(clamp(n))]


@app.get("/items")
async def list_items(limit: int = 100) -> list[Item]:
    async with get_pool().acquire() as conn:
        return [dict(r) for r in await conn.fetch(SQL_MANY, clamp(limit))]


@app.post("/items", status_code=201)
async def create_item(data: ItemIn) -> Item:
    async with get_pool().acquire() as conn:
        return dict(await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags))
