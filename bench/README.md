# Python (Litestar / FastAPI) vs Spring Boot + HikariCP

Every stack uses its latest releases and the tuning that won its sweep (Oct 2026):

- **Python 3.15.0 free-threaded (3.15t, GIL off)**, granian 2.8.4 + uvloop 0.23, asyncpg 0.32.
  Flags: `--workers 2 --runtime-mode mt --runtime-threads 2 --task-impl rust --http 1 --no-ws`
  (from [`results/granian_tuning.json`](results/granian_tuning.json)).
- **Spring Boot 4.1.1** (Spring 7.0.9, Tomcat 11.0.24, Jackson 3.1.5) on **JDK 25**, virtual threads,
  ParallelGC, **HikariCP 7.1.0**, pgjdbc 42.7.14 (from [`results/spring_tuning.json`](results/spring_tuning.json)).
- **PostgreSQL 18.4**, throughput-tuned ([`start_postgres.sh`](start_postgres.sh)).

Full tables (p50/p99, req/s, DB TPS, 64 and 256 users): [`results/RESULTS.md`](results/RESULTS.md).

| Variant | Validation | Response encoding |
|---|---|---|
| litestar + msgspec | msgspec `Struct` | msgspec |
| fastapi + msgspec | msgspec `Struct` (manual decode) | msgspec |
| fastapi + pydantic v2 | pydantic `BaseModel` | pydantic-core (`response_model`) |
| fastapi + stdlib json | `json.loads` + pydantic | `json.dumps` |
| fastapi + ujson | `ujson.loads` + pydantic | `ujson.dumps` |
| spring boot + hikaricp | Bean Validation (Hibernate Validator) | Jackson 3 |

orjson is absent because 3.13.0 refuses to build on free-threaded CPython.

## Headline: req/s at 64 users (median of 3 × 15 s)

| Endpoint | litestar + msgspec | fastapi + msgspec | fastapi + pydantic | fastapi + ujson | spring boot |
|---|---|---|---|---|---|
| GET /json | 15,894 | 14,380 | 13,750 | 14,770 | **44,528** (2.8×) |
| GET /db (1 query) | 6,072 | 5,999 | 4,978 | 5,208 | **15,142** (2.5×) |
| GET /queries?n=20 | 967 | **1,060** | 903 | 931 | 810 (0.84×) |
| GET /items?limit=100 | 2,227 | 2,292 | 1,341 | 1,788 | **3,550** (1.6×) |
| POST /items | 4,496 | 4,189 | 3,399 | 4,169 | **10,758** (2.4×) |

Spring's ratio is relative to litestar + msgspec.

**Takeaways**

- **Spring Boot leads by 1.6–2.8×** wherever framework CPU matters, with lower p50 and p99. The JVM
  JIT-compiles the whole stack; CPython 3.15t has no JIT, and granian's Rust layer covers only HTTP I/O.
- **On `/queries?n=20` Python wins** (about 19–21k DB statements/s against Spring's 16k). Each request
  makes 20 sequential round-trips to a PostgreSQL pinned to one CPU, so the database dominates. A
  likely factor is that asyncpg reuses server-side prepared statements per connection, while pgjdbc only
  switches to them after `prepareThreshold` (5) executions.
- **Best Python stacks:** Litestar + msgspec and FastAPI + msgspec are within about 5% of each other.
  Swapping pydantic for msgspec gives FastAPI +71% on 100-row lists and +20% on single queries.
- **256 users add latency, not throughput:** two server CPUs are already saturated at 64.
- **Tuning effect:** `--task-impl rust` and 2 workers were worth about 5–10% for Python. Virtual threads
  were worth up to 3.6× for Spring compared with platform threads.

## Python 3.15 GIL build vs 3.15t, JIT and orjson

Separate run at 64 users, 3 × 10 s rounds, with every stack re-measured in the same run:
[`results/gil-vs-ft/RESULTS.md`](results/gil-vs-ft/RESULTS.md). The GIL build uses granian with
4 *process* workers (`--runtime-mode mt --runtime-threads 2 --task-impl asyncio`), the winner of
[`results/granian_tuning_gil.json`](results/granian_tuning_gil.json). Total pool stays at 32.

| Endpoint (req/s) | 3.15t litestar | 3.15t fastapi+msgspec | GIL litestar | GIL fastapi+msgspec | GIL fastapi+orjson | GIL fastapi+pydantic | spring boot |
|---|---|---|---|---|---|---|---|
| GET /json | 18,411 | 14,258 | **23,187** | 16,400 | 18,234 | 16,835 | 43,825 |
| GET /db | **7,392** | 6,521 | 7,114 | 6,515 | 6,362 | 6,385 | 15,236 |
| GET /queries?n=20 | 906 | **1,178** | 1,000 | 906 | 895 | 984 | 1,000 |
| GET /items?limit=100 | 2,113 | 2,463 | **2,739** | 2,465 | 2,737 | 1,797 | 3,730 |
| POST /items | 4,522 | 4,680 | 4,810 | **4,812** | 4,481 | 4,007 | 9,860 |

- **The GIL build is the faster Python.** Litestar gains +26% on `/json` and +30% on 100-row lists over
  3.15t. DB-bound endpoints are within noise. Free-threading brings no benefit for HTTP serving, because
  granian's process workers already use every core.
- **orjson makes FastAPI's raw JSON path as fast as msgspec** (it ties GIL Litestar on 100 rows).
  pydantic remains the slowest FastAPI option for large responses.
- **The experimental JIT (`PYTHON_JIT=1`) is not usable here:** granian workers **segfaulted twice**
  (jump to address 0) during Litestar `POST /items`, which took the server down
  ([`jit_segfaults.txt`](results/gil-vs-ft/jit_segfaults.txt)). On the endpoints that completed it was
  within ±3% of JIT-off ([`jit_partial.log`](results/gil-vs-ft/jit_partial.log)).
- **Spring Boot still leads** by 1.4–2.1× over the best Python result on `/json`, `/db`, `/items` and
  `POST`. `/queries?n=20` is a tie (PostgreSQL-bound); Spring scored 810 to 1,000 across the two runs.

## Free-threading gotcha

On 3.15t, granian runs `--workers N` as **threads in one process**, each with its own event loop.
A module-global asyncpg pool gets overwritten by the next worker and used from the wrong loop
(HTTP 500s or half speed). `common.py` keeps **one pool per running event loop**.

## Methodology

- 4 vCPU VM pinned with `taskset`: server on CPUs 0–1, PostgreSQL on CPU 2, oha 1.16 on CPU 3.
- 32 PostgreSQL connections in total per stack (16 per granian worker; HikariCP max 32).
- Table reseeded (10k rows) before each stack; warmup 5 s (Python) / 30 s (JVM, for the JIT).
- Endpoints: `/json` (no DB), `/db` (1 PK lookup), `/queries?n=20` (20 lookups on one connection),
  `/items?limit=100` (one 100-row select), `POST /items` (validate + `INSERT … RETURNING`).
- Caveats: one shared cloud VM with the client on the same host, and `synchronous_commit=off`.
  Treat differences under about 10% as noise.

## Reproduce

```bash
./setup_postgres.sh                      # PostgreSQL 18.4 on :5432, db "bench" (start_postgres.sh restarts it)
uv python install 3.15.0+freethreaded
uv venv -p 3.15.0+freethreaded .venv && VIRTUAL_ENV=.venv uv pip install -r pyproject.toml
cargo install oha --locked
(cd spring && JAVA_HOME=/usr/lib/jvm/java-25-openjdk-amd64 mvn -q package -DskipTests)
.venv/bin/python tune_granian.py && .venv/bin/python tune_spring.py   # optional sweeps
.venv/bin/python run_bench.py            # defaults = tuned settings; about 1 hour
.venv/bin/python report.py               # -> results/RESULTS.md
```
