"""Robyn (Rust/actix core) + msgspec + asyncpg. Runs on Python 3.14: no 3.15 wheel exists.

Run: python apps/robyn_msgspec.py --processes N --workers 1
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robyn import Request, Response, Robyn  # noqa: E402

from apps._msgspec_io import HELLO, DecodeError, ValidationError, decode_item, encode  # noqa: E402
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, lazy_pool, random_id  # noqa: E402

app = Robyn(__file__)
HEADERS = {"Content-Type": "application/json"}


def respond(body: bytes, status: int = 200) -> Response:
    return Response(status_code=status, headers=HEADERS, description=body)


def int_param(request: Request, key: str, default: int) -> int:
    value = request.query_params.get(key, None)
    return int(value) if value else default


@app.get("/json")
def json_endpoint():
    return respond(HELLO)


@app.get("/db")
async def single_query():
    async with (await lazy_pool()).acquire() as conn:
        return respond(encode(dict(await conn.fetchrow(SQL_ONE, random_id()))))


@app.get("/queries")
async def multiple_queries(request: Request):
    n = clamp(int_param(request, "n", 20))
    async with (await lazy_pool()).acquire() as conn:
        return respond(encode([dict(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(n)]))


@app.get("/items")
async def list_items(request: Request):
    limit = clamp(int_param(request, "limit", 100))
    async with (await lazy_pool()).acquire() as conn:
        return respond(encode([dict(r) for r in await conn.fetch(SQL_MANY, limit)]))


@app.post("/items")
async def create_item(request: Request):
    body = request.body
    try:
        data = decode_item(body.encode() if isinstance(body, str) else bytes(body))
    except (ValidationError, DecodeError) as exc:
        return respond(encode({"detail": str(exc)}), 422)
    async with (await lazy_pool()).acquire() as conn:
        row = await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags)
    return respond(encode(dict(row)), 201)


if __name__ == "__main__":
    app.start(host="127.0.0.1", port=int(os.environ.get("BENCH_PORT", "8000")), _check_port=False)
