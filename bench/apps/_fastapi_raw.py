"""FastAPI app factory that bypasses pydantic response serialization.

Responses are encoded with the given `dumps`. Request bodies go through `parse`, which
must decode *and validate* (raising ValueError on bad input), since a real write endpoint
still needs validation. By default that is `loads` + pydantic `ItemIn`.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import ValidationError

from apps._fastapi_base import ItemIn, make_lifespan, row_to_dict
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, get_pool, random_id

HELLO = {"message": "Hello, World!"}


def build(label: str, dumps, loads=None, parse=None, to_obj=row_to_dict) -> FastAPI:
    if parse is None:
        def parse(body: bytes):
            return ItemIn.model_validate(loads(body))

    app = FastAPI(lifespan=make_lifespan(label), openapi_url=None, docs_url=None, redoc_url=None)

    def respond(obj, status: int = 200) -> Response:
        return Response(dumps(obj), status_code=status, media_type="application/json")

    @app.get("/json")
    async def json_endpoint():
        return respond(HELLO)

    @app.get("/db")
    async def single_query():
        async with get_pool().acquire() as conn:
            return respond(to_obj(await conn.fetchrow(SQL_ONE, random_id())))

    @app.get("/queries")
    async def multiple_queries(n: int = 20):
        async with get_pool().acquire() as conn:
            return respond([to_obj(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(clamp(n))])

    @app.get("/items")
    async def list_items(limit: int = 100):
        async with get_pool().acquire() as conn:
            return respond([to_obj(r) for r in await conn.fetch(SQL_MANY, clamp(limit))])

    @app.post("/items")
    async def create_item(request: Request):
        try:
            data = parse(await request.body())
        except (ValueError, ValidationError) as exc:
            raise HTTPException(422, str(exc)) from exc
        async with get_pool().acquire() as conn:
            row = await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags)
        return respond(to_obj(row), 201)

    return app
