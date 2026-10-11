"""Socketify.py (C++ uWebSockets server) + msgspec + asyncpg, native socketify interface.

Run: python -m socketify apps.socketify_msgspec:run --interface socketify --workers N
"""

import asyncio
import warnings

import uvloop

from apps._msgspec_io import HELLO, DecodeError, ValidationError, decode_item, encode
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, lazy_pool, random_id

with warnings.catch_warnings():  # event-loop policies are deprecated but still honoured
    warnings.simplefilter("ignore", DeprecationWarning)
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def send(res, body: bytes, status: int = 200) -> None:
    if status != 200:
        res.write_status(status)
    res.write_header("Content-Type", "application/json")
    res.cork_end(body)


def int_param(req, key: str, default: int) -> int:
    value = req.get_query(key)
    return int(value) if value else default


def json_endpoint(res, req):
    send(res, HELLO)


async def single_query(res, req):
    async with (await lazy_pool()).acquire() as conn:
        body = encode(dict(await conn.fetchrow(SQL_ONE, random_id())))
    send(res, body)


async def multiple_queries(res, req):
    n = clamp(int_param(req, "n", 20))  # req is only valid before the first await
    async with (await lazy_pool()).acquire() as conn:
        body = encode([dict(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(n)])
    send(res, body)


async def list_items(res, req):
    limit = clamp(int_param(req, "limit", 100))
    async with (await lazy_pool()).acquire() as conn:
        body = encode([dict(r) for r in await conn.fetch(SQL_MANY, limit)])
    send(res, body)


async def create_item(res, req):
    raw = (await res.get_data()).getvalue()
    try:
        data = decode_item(raw)
    except (ValidationError, DecodeError) as exc:
        send(res, encode({"detail": str(exc)}), 422)
        return
    async with (await lazy_pool()).acquire() as conn:
        row = await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags)
    send(res, encode(dict(row)), 201)


def run(app):
    # socketify 0.0.31 installs a task factory without **kwargs; asyncio on 3.14+ passes
    # eager_start=..., so every create_task() raised TypeError. The factory only wrapped
    # asyncio's own Task, so the default factory is behaviourally identical.
    app.loop.loop.set_task_factory(None)
    app.get("/json", json_endpoint)
    app.get("/db", single_query)
    app.get("/queries", multiple_queries)
    app.get("/items", list_items)
    app.post("/items", create_item)
