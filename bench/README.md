# Litestar + msgspec vs FastAPI (pydantic v2 / json / ujson)

Python **3.15.0 free-threaded (3.15t, GIL off)** · **granian 2.8.4** ASGI + **uvloop 0.23** ·
**asyncpg 0.32** · **PostgreSQL 18.4**. All libraries are at their latest PyPI releases (Oct 2026).
Full numbers: [`results/RESULTS.md`](results/RESULTS.md) (raw: `results/results.json`).

| Variant | Request validation | Response encoding |
|---|---|---|
| litestar + msgspec | msgspec `Struct` + `Meta` constraints | msgspec |
| fastapi + pydantic v2 | pydantic `BaseModel` | pydantic-core via return-type `response_model` |
| fastapi + stdlib json | `json.loads` + pydantic `model_validate` | `json.dumps` → `Response` |
| fastapi + ujson | `ujson.loads` + pydantic `model_validate` | `ujson.dumps` → `Response` |

orjson is not included: orjson 3.13.0 refuses to build on free-threaded CPython.

## Headline (req/s, median of 3 × 15 s, 64 connections)

| Endpoint | litestar + msgspec | fastapi + pydantic v2 | fastapi + json | fastapi + ujson |
|---|---|---|---|---|
| GET /json | **16,503** | 12,734 | 12,845 | 12,850 |
| GET /db (1 query) | **6,123** | 5,505 | 4,767 | 4,905 |
| GET /queries?n=20 | 884 | **1,021** | 824 | 953 |
| GET /items?limit=100 | **2,000** | 1,377 | 1,406 | 1,732 |
| POST /items | **4,557** | 3,567 | 3,638 | 4,166 |

**Takeaways**

- Litestar + msgspec wins 4 of 5 endpoints: about **+30%** on framework overhead (`/json`), **+45%** on
  serializing 100 rows, **+28%** on validated inserts, and **+11%** on a single query.
- `/queries?n=20` is bound by 20 sequential DB round-trips, so the framework barely matters.
  The spread there (≈ ±10%) is within run-to-run noise; see the per-round table.
- Within FastAPI, **ujson is the best encoder** for larger payloads (+26% on 100 rows vs pydantic),
  while stdlib json is no faster than pydantic v2. For small responses, all three tie.
- The FastAPI json/ujson variants must turn `datetime` into strings by hand, which pydantic and
  msgspec do natively.

## Free-threading gotcha (important if you deploy this)

On 3.15t, granian runs `--workers N` as **threads in one process**, each with its own event loop,
not as separate processes. Module-level state is therefore shared between workers. A global
asyncpg pool created in lifespan gets overwritten by the next worker and then used from the wrong
loop: Litestar returned mostly HTTP 500s, and FastAPI ran at roughly half speed. `common.py`
keeps **one pool per running event loop**.

## Setup / methodology

- 4 vCPU box, pinned with `taskset`: granian (2 workers) on CPUs 0–1, PostgreSQL on CPU 2,
  oha 1.16 on CPU 3. Pool of 16 connections per worker. Table reseeded (10k rows) before each app.
- Endpoints: `/json` (no DB), `/db` (1 PK lookup), `/queries?n=20` (20 lookups),
  `/items?limit=100` (one 100-row select), `POST /items` (validate + `INSERT … RETURNING`).
- Caveats: this is one shared cloud VM with the client on the same host, and PostgreSQL uses
  `synchronous_commit=off`. Treat differences under ~10% as noise. granian still labels free-threaded
  support "experimental".

## Reproduce

```bash
./setup_postgres.sh                      # PostgreSQL 18.4 on :5432, db "bench"
uv python install 3.15.0+freethreaded
uv venv -p 3.15.0+freethreaded .venv && VIRTUAL_ENV=.venv uv pip install -r pyproject.toml
cargo install oha --locked
.venv/bin/python run_bench.py --duration 15 --warmup 5 --rounds 3
.venv/bin/python report.py               # -> results/RESULTS.md
```
