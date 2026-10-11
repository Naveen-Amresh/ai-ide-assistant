"""BlackSheep (Cython core) + msgspec + asyncpg, served by granian (ASGI)."""

from blacksheep import Application, Content, Request, Response

from apps._msgspec_io import HELLO, DecodeError, ValidationError, decode_item, encode
from common import SQL_INSERT, SQL_MANY, SQL_ONE, clamp, close_pool, open_pool, get_pool, random_id

app = Application()
JSON = b"application/json"


def respond(body: bytes, status: int = 200) -> Response:
    return Response(status, None, Content(JSON, body))


def int_param(request: Request, key: str, default: int) -> int:
    values = request.query.get(key)
    return int(values[0]) if values else default


@app.router.get("/json")
async def json_endpoint() -> Response:
    return respond(HELLO)


@app.router.get("/db")
async def single_query() -> Response:
    async with get_pool().acquire() as conn:
        return respond(encode(dict(await conn.fetchrow(SQL_ONE, random_id()))))


@app.router.get("/queries")
async def multiple_queries(request: Request) -> Response:
    n = clamp(int_param(request, "n", 20))
    async with get_pool().acquire() as conn:
        return respond(encode([dict(await conn.fetchrow(SQL_ONE, random_id())) for _ in range(n)]))


@app.router.get("/items")
async def list_items(request: Request) -> Response:
    limit = clamp(int_param(request, "limit", 100))
    async with get_pool().acquire() as conn:
        return respond(encode([dict(r) for r in await conn.fetch(SQL_MANY, limit)]))


@app.router.post("/items")
async def create_item(request: Request) -> Response:
    try:
        data = decode_item(await request.read())
    except (ValidationError, DecodeError) as exc:
        return respond(encode({"detail": str(exc)}), 422)
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(SQL_INSERT, data.name, data.price, data.quantity, data.tags)
    return respond(encode(dict(row)), 201)


async def _start(_app: Application) -> None:
    await open_pool()


async def _stop(_app: Application) -> None:
    await close_pool()


app.on_start += _start
app.on_stop += _stop
