"""Emmett55 + msgspec + asyncpg, served by granian's native RSGI interface (no ASGI layer)."""

from emmett55 import App, request, response

from apps._msgspec_io import HELLO, DecodeError, ValidationError, decode_item, encode
from common import (EXPORT_MAX, SQL_AGG_MANY, SQL_AGG_ONE, SQL_INSERT, SQL_MANY, SQL_ONE, clamp,
                    lazy_pool, random_id)

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


@app.route("/export", methods=["get"], output="bytes")
async def export_rows():
    _json()
    rows = clamp(int_param("rows", EXPORT_MAX), hi=EXPORT_MAX)
    async with (await lazy_pool()).acquire() as conn:
        return encode([dict(r) for r in await conn.fetch(SQL_MANY, rows)])


# --- json_agg variants: PostgreSQL renders the JSON, Python forwards the text ---

@app.route("/agg/json", methods=["get"], output="bytes")
async def agg_json_endpoint():
    _json()
    return HELLO


@app.route("/agg/db", methods=["get"], output="bytes")
async def agg_single_query():
    _json()
    async with (await lazy_pool()).acquire() as conn:
        return (await conn.fetchval(SQL_AGG_ONE, random_id())).encode()


@app.route("/agg/items", methods=["get"], output="bytes")
async def agg_list_items():
    _json()
    limit = clamp(int_param("limit", 100))
    async with (await lazy_pool()).acquire() as conn:
        return (await conn.fetchval(SQL_AGG_MANY, limit)).encode()


@app.route("/agg/export", methods=["get"], output="bytes")
async def agg_export_rows():
    _json()
    rows = clamp(int_param("rows", EXPORT_MAX), hi=EXPORT_MAX)
    async with (await lazy_pool()).acquire() as conn:
        return (await conn.fetchval(SQL_AGG_MANY, rows)).encode()
