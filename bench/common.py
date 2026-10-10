"""Shared settings and SQL used by every benchmarked app."""

import asyncio
import os
import random

import asyncpg

DSN = os.environ.get("BENCH_DSN", "postgresql://postgres@127.0.0.1:5432/bench")
POOL_SIZE = int(os.environ.get("BENCH_POOL_SIZE", "16"))
ROWS = 10_000

SQL_ONE = "SELECT id, name, price, quantity, tags, created_at FROM items WHERE id = $1"
SQL_MANY = "SELECT id, name, price, quantity, tags, created_at FROM items ORDER BY id LIMIT $1"
SQL_INSERT = (
    "INSERT INTO items (name, price, quantity, tags) VALUES ($1, $2, $3, $4) "
    "RETURNING id, name, price, quantity, tags, created_at"
)


def random_id() -> int:
    return random.randint(1, ROWS)


def clamp(n: int, lo: int = 1, hi: int = 500) -> int:
    return max(lo, min(hi, n))


# On free-threaded builds granian runs workers as *threads in one process*, each with
# its own event loop, so module globals are shared between workers. An asyncpg pool is
# bound to the loop that created it, therefore keep one pool per running loop.
_pools: dict[asyncio.AbstractEventLoop, asyncpg.Pool] = {}


async def open_pool():
    pool = await asyncpg.create_pool(DSN, min_size=POOL_SIZE, max_size=POOL_SIZE)
    _pools[asyncio.get_running_loop()] = pool
    return pool


async def close_pool() -> None:
    await _pools.pop(asyncio.get_running_loop()).close()


def get_pool():
    return _pools[asyncio.get_running_loop()]
