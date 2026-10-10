"""FastAPI + ujson + asyncpg."""

import ujson

from apps._fastapi_raw import build

app = build("fastapi-ujson", ujson.dumps, ujson.loads)
