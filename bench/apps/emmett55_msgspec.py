"""Emmett55 + msgspec + asyncpg, served by granian's native RSGI interface (no ASGI layer)."""

from emmett55 import App, request, response

from apps._msgspec_io import HELLO, DecodeError, ValidationError, decode_item, encode
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, lazy_pool, random_id

app = App(__name__)


def _json() -> None:
    response.content_type = "application/json"


def int_param(key: str, default: int) -> int:
    value = request.query_params.get(key)
    return int(value) if value else default


@app.route("/json", methods=["get"], output="bytes")
async def json_endpoint():
    _json()
    return HELLO


@app.route("/db", methods=["get"], output="bytes")
async def single_query():
    _json()
    async with (await lazy_pool()).acquire() as conn:
        return encode(dict(await conn.fetchrow(SQL_ONE, random_id())))


@app.route("/queries", methods=["get"], output="bytes")
async def multiple_queries():
    _json()
    n = clamp(int_param("n", 20))
    async with (await lazy_pool()).acquire() as conn:
        return encode([dict(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(n)])


@app.route("/items", methods=["get"], output="bytes")
async def list_items():
    _json()
    limit = clamp(int_param("limit", 100))
    async with (await lazy_pool()).acquire() as conn:
        return encode([dict(r) for r in await conn.fetch(SQL_MANY, limit)])


@app.route("/items", methods=["post"], output="bytes", name="create_item")
async def create_item():
    _json()
    try:
        data = decode_item(await request.body)
    except (ValidationError, DecodeError) as exc:
        response.status = 422
        return encode({"detail": str(exc)})
    async with (await lazy_pool()).acquire() as conn:
        row = await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags)
    response.status = 201
    return encode(dict(row))
