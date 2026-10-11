"""Emmett55 (granian RSGI) + Polars + ADBC: PostgreSQL -> Arrow -> Polars -> JSON, no Python row objects.

ADBC is a blocking driver, so queries run on a per-worker thread pool with one ADBC
connection per thread (BENCH_POOL_SIZE threads, same connection budget as asyncpg).
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import adbc_driver_postgresql.dbapi as adbc
import polars as pl
from emmett55 import App, request, response

from apps._msgspec_io import HELLO
from common import DSN, EXPORT_MAX, POOL_SIZE, SQL_MANY, SQL_ONE, clamp, random_id

app = App(__name__)
_executor = ThreadPoolExecutor(max_workers=POOL_SIZE, thread_name_prefix="adbc")
_local = threading.local()


def _query_json(sql: str, params: tuple) -> bytes:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _local.conn = adbc.connect(DSN, autocommit=True)
    with conn.cursor() as cur:
        cur.execute(sql, parameters=params)
        table = cur.fetch_arrow_table()
    return pl.from_arrow(table).write_json().encode()


async def query_json(sql: str, *params) -> bytes:
    return await asyncio.get_running_loop().run_in_executor(_executor, _query_json, sql, params)


def _json() -> None:
    response.content_type = "application/json"


def int_param(key: str, default: int) -> int:
    value = request.query_params.get(key)
    return int(value) if value else default


@app.route("/json", methods=["get"], output="bytes")
async def json_endpoint():
    _json()
    return HELLO


@app.route("/polars/db", methods=["get"], output="bytes")
async def single_query():
    _json()
    return (await query_json(SQL_ONE, random_id()))[1:-1]  # one-row array -> object


@app.route("/polars/items", methods=["get"], output="bytes")
async def list_items():
    _json()
    return await query_json(SQL_MANY, clamp(int_param("limit", 100)))


@app.route("/polars/export", methods=["get"], output="bytes")
async def export_rows():
    _json()
    return await query_json(SQL_MANY, clamp(int_param("rows", EXPORT_MAX), hi=EXPORT_MAX))
