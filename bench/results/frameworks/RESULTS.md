# Results

Users = concurrent keep-alive connections. Req/s = HTTP throughput. DB TPS = database statements per second (req/s x statements per request). Values are medians of the rounds; best req/s per endpoint and user count in bold.

## GET /json

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] litestar + msgspec | 64 | 2.29 | 6.71 | 25,113 | 0 (no DB) |
| [gil] blacksheep + msgspec | 64 | 0.96 | 4.89 | 52,820 | 0 (no DB) |
| [gil] emmett55 + msgspec (rsgi) | 64 | 1.09 | 4.26 | 50,694 | 0 (no DB) |
| [gil] socketify + msgspec | 64 | 0.15 | 10.57 | **98,522** | 0 (no DB) |
| [3.14] robyn + msgspec | 64 | 1.94 | 5.29 | 36,809 | 0 (no DB) |
| spring boot + hikaricp | 64 | 1.13 | 4.18 | 51,502 | 0 (no DB) |

## GET /db (1 query)

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] litestar + msgspec | 64 | 7.12 | 20.61 | 8,144 | 8,144 |
| [gil] blacksheep + msgspec | 64 | 5.73 | 17.39 | 10,017 | 10,017 |
| [gil] emmett55 + msgspec (rsgi) | 64 | 5.50 | 15.53 | 10,580 | 10,580 |
| [gil] socketify + msgspec | 64 | 4.24 | 26.02 | 10,598 | 10,598 |
| [3.14] robyn + msgspec | 64 | 5.54 | 17.48 | 9,932 | 9,932 |
| spring boot + hikaricp | 64 | 3.20 | 10.37 | **17,756** | 17,756 |

## GET /queries?n=20

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] litestar + msgspec | 64 | 50.76 | 109.32 | 1,190 | 23,793 |
| [gil] blacksheep + msgspec | 64 | 52.76 | 119.46 | 1,135 | 22,703 |
| [gil] emmett55 + msgspec (rsgi) | 64 | 55.76 | 122.31 | 1,125 | 22,495 |
| [gil] socketify + msgspec | 64 | 46.46 | 96.13 | **1,331** | 26,628 |
| [3.14] robyn + msgspec | 64 | 53.60 | 174.32 | 1,009 | 20,178 |
| spring boot + hikaricp | 64 | 63.94 | 136.57 | 912 | 18,238 |

## GET /items?limit=100

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] litestar + msgspec | 64 | 19.55 | 54.82 | 3,037 | 3,037 |
| [gil] blacksheep + msgspec | 64 | 15.08 | 49.02 | 3,862 | 3,862 |
| [gil] emmett55 + msgspec (rsgi) | 64 | 13.79 | 44.66 | 4,123 | 4,123 |
| [gil] socketify + msgspec | 64 | 12.28 | 62.93 | 3,824 | 3,824 |
| [3.14] robyn + msgspec | 64 | 13.24 | 50.54 | 3,608 | 3,608 |
| spring boot + hikaricp | 64 | 11.32 | 33.15 | **5,077** | 5,077 |

## POST /items

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] litestar + msgspec | 64 | 10.81 | 26.45 | 5,472 | 5,472 |
| [gil] blacksheep + msgspec | 64 | 7.48 | 20.45 | 7,840 | 7,840 |
| [gil] emmett55 + msgspec (rsgi) | 64 | 6.50 | 16.41 | 9,122 | 9,122 |
| [gil] socketify + msgspec | 64 | 5.72 | 26.36 | 8,668 | 8,668 |
| [3.14] robyn + msgspec | 64 | 7.61 | 25.32 | 7,333 | 7,333 |
| spring boot + hikaricp | 64 | 4.56 | 17.56 | **11,882** | 11,882 |

## Summary: req/s relative to [gil] litestar + msgspec

| Endpoint | Users | [gil] litestar + msgspec | [gil] blacksheep + msgspec | [gil] emmett55 + msgspec (rsgi) | [gil] socketify + msgspec | [3.14] robyn + msgspec | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|
| GET /json | 64 | 1.00x | 2.10x | 2.02x | 3.92x | 1.47x | 2.05x |
| GET /db (1 query) | 64 | 1.00x | 1.23x | 1.30x | 1.30x | 1.22x | 2.18x |
| GET /queries?n=20 | 64 | 1.00x | 0.95x | 0.95x | 1.12x | 0.85x | 0.77x |
| GET /items?limit=100 | 64 | 1.00x | 1.27x | 1.36x | 1.26x | 1.19x | 1.67x |
| POST /items | 64 | 1.00x | 1.43x | 1.67x | 1.58x | 1.34x | 2.17x |

## Per-round req/s (run-to-run noise)

| Endpoint | Users | [gil] litestar + msgspec | [gil] blacksheep + msgspec | [gil] emmett55 + msgspec (rsgi) | [gil] socketify + msgspec | [3.14] robyn + msgspec | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|
| GET /json | 64 | 25,113, 26,915, 24,881 | 54,880, 52,820, 52,428 | 50,236, 53,083, 50,694 | 98,522, 99,808, 98,076 | 36,809, 37,439, 29,717 | 51,502, 53,601, 47,741 |
| GET /db (1 query) | 64 | 8,578, 8,069, 8,144 | 10,918, 9,640, 10,017 | 10,580, 9,858, 11,103 | 10,153, 10,746, 10,598 | 9,932, 11,340, 9,894 | 18,501, 14,225, 17,756 |
| GET /queries?n=20 | 64 | 1,258, 1,187, 1,190 | 1,135, 1,135, 1,170 | 1,129, 1,102, 1,125 | 1,351, 1,231, 1,331 | 988, 1,009, 1,109 | 973, 899, 912 |
| GET /items?limit=100 | 64 | 3,037, 2,964, 3,089 | 3,360, 3,862, 4,016 | 4,060, 4,272, 4,123 | 3,754, 3,824, 3,846 | 3,608, 3,888, 3,259 | 5,222, 5,077, 4,986 |
| POST /items | 64 | 5,424, 5,472, 5,853 | 7,569, 7,840, 7,973 | 8,633, 9,460, 9,122 | 9,286, 8,668, 8,195 | 6,960, 7,333, 7,694 | 11,808, 12,046, 11,882 |

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
