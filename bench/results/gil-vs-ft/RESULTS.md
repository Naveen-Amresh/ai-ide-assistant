# Results

Users = concurrent keep-alive connections. Req/s = HTTP throughput. DB TPS = database statements per second (req/s x statements per request). Values are medians of the rounds; best req/s per endpoint and user count in bold.

## GET /json

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 3.00 | 10.96 | 18,411 | 0 (no DB) |
| fastapi + msgspec | 64 | 4.08 | 12.83 | 14,258 | 0 (no DB) |
| [gil] litestar + msgspec | 64 | 2.54 | 7.50 | 23,187 | 0 (no DB) |
| [gil] fastapi + msgspec | 64 | 3.59 | 10.03 | 16,400 | 0 (no DB) |
| [gil] fastapi + orjson | 64 | 3.10 | 9.20 | 18,234 | 0 (no DB) |
| [gil] fastapi + pydantic v2 | 64 | 3.45 | 9.34 | 16,835 | 0 (no DB) |
| spring boot + hikaricp | 64 | 1.29 | 4.68 | **43,825** | 0 (no DB) |

## GET /db (1 query)

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 7.98 | 21.37 | 7,392 | 7,392 |
| fastapi + msgspec | 64 | 9.05 | 23.90 | 6,521 | 6,521 |
| [gil] litestar + msgspec | 64 | 8.19 | 23.54 | 7,114 | 7,114 |
| [gil] fastapi + msgspec | 64 | 8.97 | 26.26 | 6,515 | 6,515 |
| [gil] fastapi + orjson | 64 | 9.04 | 27.06 | 6,362 | 6,362 |
| [gil] fastapi + pydantic v2 | 64 | 9.45 | 24.08 | 6,385 | 6,385 |
| spring boot + hikaricp | 64 | 3.76 | 11.51 | **15,236** | 15,236 |

## GET /queries?n=20

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 68.08 | 142.32 | 906 | 18,118 |
| fastapi + msgspec | 64 | 50.86 | 112.39 | **1,178** | 23,557 |
| [gil] litestar + msgspec | 64 | 59.91 | 147.63 | 1,000 | 20,000 |
| [gil] fastapi + msgspec | 64 | 65.33 | 163.70 | 906 | 18,113 |
| [gil] fastapi + orjson | 64 | 66.50 | 154.59 | 895 | 17,901 |
| [gil] fastapi + pydantic v2 | 64 | 61.05 | 147.24 | 984 | 19,681 |
| spring boot + hikaricp | 64 | 59.61 | 115.17 | 1,000 | 20,008 |

## GET /items?limit=100

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 28.22 | 70.73 | 2,113 | 2,113 |
| fastapi + msgspec | 64 | 23.43 | 63.19 | 2,463 | 2,463 |
| [gil] litestar + msgspec | 64 | 20.96 | 64.18 | 2,739 | 2,739 |
| [gil] fastapi + msgspec | 64 | 23.96 | 64.15 | 2,465 | 2,465 |
| [gil] fastapi + orjson | 64 | 21.20 | 60.67 | 2,737 | 2,737 |
| [gil] fastapi + pydantic v2 | 64 | 31.82 | 104.04 | 1,797 | 1,797 |
| spring boot + hikaricp | 64 | 15.38 | 44.19 | **3,730** | 3,730 |

## POST /items

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 13.13 | 30.82 | 4,522 | 4,522 |
| fastapi + msgspec | 64 | 12.36 | 29.92 | 4,680 | 4,680 |
| [gil] litestar + msgspec | 64 | 12.12 | 31.57 | 4,810 | 4,810 |
| [gil] fastapi + msgspec | 64 | 12.22 | 31.49 | 4,812 | 4,812 |
| [gil] fastapi + orjson | 64 | 13.42 | 30.79 | 4,481 | 4,481 |
| [gil] fastapi + pydantic v2 | 64 | 14.72 | 34.80 | 4,007 | 4,007 |
| spring boot + hikaricp | 64 | 5.38 | 22.20 | **9,860** | 9,860 |

## Summary: req/s relative to litestar + msgspec

| Endpoint | Users | litestar + msgspec | fastapi + msgspec | [gil] litestar + msgspec | [gil] fastapi + msgspec | [gil] fastapi + orjson | [gil] fastapi + pydantic v2 | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|---|
| GET /json | 64 | 1.00x | 0.77x | 1.26x | 0.89x | 0.99x | 0.91x | 2.38x |
| GET /db (1 query) | 64 | 1.00x | 0.88x | 0.96x | 0.88x | 0.86x | 0.86x | 2.06x |
| GET /queries?n=20 | 64 | 1.00x | 1.30x | 1.10x | 1.00x | 0.99x | 1.09x | 1.10x |
| GET /items?limit=100 | 64 | 1.00x | 1.17x | 1.30x | 1.17x | 1.30x | 0.85x | 1.77x |
| POST /items | 64 | 1.00x | 1.03x | 1.06x | 1.06x | 0.99x | 0.89x | 2.18x |

## Per-round req/s (run-to-run noise)

| Endpoint | Users | litestar + msgspec | fastapi + msgspec | [gil] litestar + msgspec | [gil] fastapi + msgspec | [gil] fastapi + orjson | [gil] fastapi + pydantic v2 | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|---|
| GET /json | 64 | 18,411, 18,578, 17,492 | 14,258, 15,553, 13,699 | 22,485, 24,398, 23,187 | 16,167, 16,400, 16,893 | 19,463, 18,234, 16,777 | 16,835, 16,626, 17,790 | 42,093, 43,890, 43,825 |
| GET /db (1 query) | 64 | 6,733, 7,865, 7,392 | 6,521, 6,573, 5,911 | 7,046, 7,114, 7,133 | 6,515, 6,923, 6,266 | 6,576, 6,262, 6,362 | 6,385, 6,179, 6,519 | 17,051, 15,078, 15,236 |
| GET /queries?n=20 | 64 | 893, 945, 906 | 1,178, 1,234, 1,126 | 919, 1,034, 1,000 | 909, 891, 906 | 1,031, 895, 889 | 1,035, 984, 955 | 924, 1,000, 1,017 |
| GET /items?limit=100 | 64 | 2,113, 2,106, 2,132 | 2,433, 2,463, 2,619 | 2,780, 2,570, 2,739 | 2,465, 2,755, 2,154 | 2,580, 2,737, 2,764 | 1,862, 1,758, 1,797 | 3,631, 4,190, 3,730 |
| POST /items | 64 | 4,492, 4,522, 4,544 | 4,680, 4,727, 4,592 | 5,186, 4,343, 4,810 | 4,273, 4,812, 4,879 | 4,354, 4,572, 4,481 | 4,007, 4,224, 3,807 | 8,984, 9,860, 10,858 |

All responses 2xx.

## Environment

- Python: `3.15.0 free-threading build (main, Oct  9 2026, 15:24:59) [Clang 22.1.3 ]` (GIL enabled: False)
- Java: `openjdk version "25.0.4.1" 2026-08-18`, JVM opts `-XX:+UseParallelGC -Xms1g -Xmx1g -XX:+AlwaysPreTouch`, virtual threads: True
- PostgreSQL: 18.4
- Kernel: 6.18.44-fc-v114, 4 vCPU; load generator: oha 1.16.0
- Server CPUs `0,1`, PostgreSQL CPUs `2`, oha CPUs `3`; 32 PostgreSQL connections in total per stack
- granian flags: `--interface asgi --loop uvloop --http 1 --no-ws --workers 2 --runtime-mode mt --runtime-threads 2 --task-impl rust --log-level warning --no-access-log`
- 3 x 10s rounds after 5s warmup (30s for the JVM)
- Python packages: litestar 2.24.0, msgspec 0.22.0, fastapi 0.143.0, starlette 1.7.0, pydantic 2.14.0, pydantic-core 2.50.0, ujson 6.0.0, granian 2.8.4, uvloop 0.23.0, asyncpg 0.32.0
- Java stack: Spring Boot 4.1.1 (Spring 7.0.9, Tomcat 11.0.24, Jackson 3.1.5), HikariCP 7.1.0, pgjdbc 42.7.14, Hibernate Validator 9.1.3
