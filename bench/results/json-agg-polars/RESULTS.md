# Results

Users = concurrent keep-alive connections. Req/s = HTTP throughput. DB TPS = database statements per second (req/s x statements per request). Values are medians of the rounds; best req/s per endpoint and user count in bold.

## GET /db (1 query)

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] emmett55 + msgspec (rsgi) | 64 | 5.30 | 14.38 | 11,074 | 11,074 |
| [gil] emmett55 + json_agg (rsgi) | 64 | 5.60 | 17.25 | 10,251 | 10,251 |
| [gil] emmett55 + polars/adbc (rsgi) | 64 | 23.80 | 51.38 | 2,589 | 2,589 |
| spring boot + hikaricp | 64 | 3.30 | 10.99 | **16,703** | 16,703 |
| spring boot + json_agg | 64 | 3.45 | 12.65 | 15,922 | 15,922 |

## GET /items?limit=100

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] emmett55 + msgspec (rsgi) | 64 | 15.13 | 39.80 | 3,884 | 3,884 |
| [gil] emmett55 + json_agg (rsgi) | 64 | 34.47 | 69.50 | 1,795 | 1,795 |
| [gil] emmett55 + polars/adbc (rsgi) | 64 | 32.31 | 67.14 | 1,879 | 1,879 |
| spring boot + hikaricp | 64 | 11.81 | 35.26 | **4,814** | 4,814 |
| spring boot + json_agg | 64 | 28.09 | 64.06 | 2,117 | 2,117 |

## GET /export?rows=10000

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| [gil] emmett55 + msgspec (rsgi) | 64 | 924.21 | 2360.64 | 65 | 65 |
| [gil] emmett55 + json_agg (rsgi) | 64 | 1900.95 | 4238.92 | 33 | 33 |
| [gil] emmett55 + polars/adbc (rsgi) | 64 | 654.20 | 1186.81 | **98** | 98 |
| spring boot + hikaricp | 64 | 784.26 | 1404.77 | 83 | 83 |
| spring boot + json_agg | 64 | 2061.76 | 4034.17 | 31 | 31 |

## Summary: req/s relative to [gil] emmett55 + msgspec (rsgi)

| Endpoint | Users | [gil] emmett55 + msgspec (rsgi) | [gil] emmett55 + json_agg (rsgi) | [gil] emmett55 + polars/adbc (rsgi) | spring boot + hikaricp | spring boot + json_agg |
|---|---|---|---|---|---|---|
| GET /db (1 query) | 64 | 1.00x | 0.93x | 0.23x | 1.51x | 1.44x |
| GET /items?limit=100 | 64 | 1.00x | 0.46x | 0.48x | 1.24x | 0.55x |
| GET /export?rows=10000 | 64 | 1.00x | 0.51x | 1.50x | 1.28x | 0.48x |

## Per-round req/s (run-to-run noise)

| Endpoint | Users | [gil] emmett55 + msgspec (rsgi) | [gil] emmett55 + json_agg (rsgi) | [gil] emmett55 + polars/adbc (rsgi) | spring boot + hikaricp | spring boot + json_agg |
|---|---|---|---|---|---|---|
| GET /db (1 query) | 64 | 11,074, 10,857, 11,216 | 10,251, 9,983, 10,753 | 2,322, 2,589, 2,716 | 16,703, 16,331, 19,199 | 17,249, 15,922, 15,784 |
| GET /items?limit=100 | 64 | 3,884, 3,764, 4,144 | 1,866, 1,763, 1,795 | 1,839, 2,037, 1,879 | 4,879, 4,814, 4,553 | 2,119, 2,060, 2,117 |
| GET /export?rows=10000 | 64 | 67, 65, 64 | 32, 33, 33 | 98, 94, 98 | 84, 81, 83 | 31, 31, 32 |

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
