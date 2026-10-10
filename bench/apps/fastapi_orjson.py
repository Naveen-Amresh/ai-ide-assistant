"""FastAPI + orjson + asyncpg (GIL build only: orjson does not support free-threaded CPython)."""

import orjson

from apps._fastapi_raw import build

# orjson encodes datetime natively, so rows only need dict(), no isoformat() pass.
app = build("fastapi-orjson", orjson.dumps, orjson.loads, to_obj=dict)
