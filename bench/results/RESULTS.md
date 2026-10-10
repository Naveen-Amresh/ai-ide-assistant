# Results

## Throughput (req/s, median of rounds; higher is better)

| Endpoint | litestar + msgspec | fastapi + pydantic v2 | fastapi + stdlib json | fastapi + ujson |
|---|---|---|---|---|
| GET /json | **16,503 (1.30x)** | 12,734 (1.00x) | 12,845 (1.01x) | 12,850 (1.01x) |
| GET /db (1 query) | **6,123 (1.11x)** | 5,505 (1.00x) | 4,767 (0.87x) | 4,905 (0.89x) |
| GET /queries?n=20 | 884 (0.87x) | **1,021 (1.00x)** | 824 (0.81x) | 953 (0.93x) |
| GET /items?limit=100 | **2,000 (1.45x)** | 1,377 (1.00x) | 1,406 (1.02x) | 1,732 (1.26x) |
| POST /items | **4,557 (1.28x)** | 3,567 (1.00x) | 3,638 (1.02x) | 4,166 (1.17x) |

Ratios are relative to `fastapi + pydantic v2`. Best per row in bold.

## Latency p50 / p99 (ms; lower is better)

| Endpoint | litestar + msgspec | fastapi + pydantic v2 | fastapi + stdlib json | fastapi + ujson |
|---|---|---|---|---|
| GET /json | 3.46 / 11.49 | 4.68 / 12.35 | 4.59 / 12.60 | 4.56 / 13.06 |
| GET /db (1 query) | 9.95 / 24.39 | 10.78 / 29.41 | 12.13 / 28.62 | 12.48 / 27.37 |
| GET /queries?n=20 | 67.22 / 149.05 | 59.15 / 130.38 | 77.60 / 156.14 | 60.50 / 163.39 |
| GET /items?limit=100 | 30.06 / 77.04 | 42.79 / 107.37 | 40.12 / 139.82 | 33.20 / 99.87 |
| POST /items | 13.31 / 27.77 | 17.32 / 31.62 | 16.99 / 34.00 | 14.51 / 33.33 |

## Per-round req/s (run-to-run noise)

| Endpoint | litestar + msgspec | fastapi + pydantic v2 | fastapi + stdlib json | fastapi + ujson |
|---|---|---|---|---|
| GET /json | 15,502, 16,606, 16,503 | 13,155, 12,547, 12,734 | 11,817, 13,257, 12,845 | 12,850, 12,470, 13,486 |
| GET /db (1 query) | 5,968, 6,244, 6,123 | 5,692, 5,505, 5,465 | 5,315, 4,633, 4,767 | 5,234, 4,905, 4,780 |
| GET /queries?n=20 | 960, 884, 877 | 985, 1,068, 1,021 | 824, 701, 825 | 784, 997, 953 |
| GET /items?limit=100 | 1,872, 2,000, 2,009 | 1,312, 1,431, 1,377 | 1,494, 1,406, 1,275 | 1,699, 1,732, 1,743 |
| POST /items | 4,138, 4,557, 4,732 | 3,757, 3,542, 3,567 | 3,491, 3,658, 3,638 | 4,166, 3,971, 4,219 |

All responses 2xx.

## Environment

- Python: `3.15.0 free-threading build (main, Oct  9 2026, 15:24:59) [Clang 22.1.3 ]` (GIL enabled: False)
- PostgreSQL: 18.4
- Kernel: 6.18.44-fc-v114, 4 vCPU; load generator: oha 1.16.0
- granian: 2 workers (threads on free-threaded Python), ASGI, uvloop, server CPUs `0,1`, PostgreSQL CPUs `2`, oha CPUs `3`
- 64 connections, 3 x 15s rounds after 5s warmup
- Packages: litestar 2.24.0, msgspec 0.22.0, fastapi 0.143.0, starlette 1.7.0, pydantic 2.14.0, pydantic-core 2.50.0, ujson 6.0.0, granian 2.8.4, uvloop 0.23.0, asyncpg 0.32.0
