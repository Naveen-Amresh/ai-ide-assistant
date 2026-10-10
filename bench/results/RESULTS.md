# Results

Users = concurrent keep-alive connections. Req/s = HTTP throughput. DB TPS = database statements per second (req/s x statements per request). Values are medians of the rounds; best req/s per endpoint and user count in bold.

## GET /json

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 3.59 | 10.59 | 15,894 | 0 (no DB) |
| fastapi + msgspec | 64 | 3.96 | 11.95 | 14,380 | 0 (no DB) |
| fastapi + pydantic v2 | 64 | 4.31 | 11.64 | 13,750 | 0 (no DB) |
| fastapi + stdlib json | 64 | 4.26 | 11.86 | 13,588 | 0 (no DB) |
| fastapi + ujson | 64 | 3.95 | 12.47 | 14,770 | 0 (no DB) |
| spring boot + hikaricp | 64 | 1.23 | 4.79 | **44,528** | 0 (no DB) |
| litestar + msgspec | 256 | 14.08 | 32.31 | 17,213 | 0 (no DB) |
| fastapi + msgspec | 256 | 18.19 | 36.23 | 13,576 | 0 (no DB) |
| fastapi + pydantic v2 | 256 | 17.72 | 36.00 | 13,454 | 0 (no DB) |
| fastapi + stdlib json | 256 | 18.50 | 39.81 | 13,175 | 0 (no DB) |
| fastapi + ujson | 256 | 16.36 | 34.98 | 14,488 | 0 (no DB) |
| spring boot + hikaricp | 256 | 4.95 | 17.59 | **45,093** | 0 (no DB) |

## GET /db (1 query)

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 9.47 | 25.86 | 6,072 | 6,072 |
| fastapi + msgspec | 64 | 9.80 | 24.43 | 5,999 | 5,999 |
| fastapi + pydantic v2 | 64 | 12.03 | 27.81 | 4,978 | 4,978 |
| fastapi + stdlib json | 64 | 13.00 | 31.73 | 4,585 | 4,585 |
| fastapi + ujson | 64 | 11.66 | 26.35 | 5,208 | 5,208 |
| spring boot + hikaricp | 64 | 3.84 | 11.37 | **15,142** | 15,142 |
| litestar + msgspec | 256 | 35.91 | 154.26 | 6,127 | 6,127 |
| fastapi + msgspec | 256 | 36.13 | 165.36 | 5,987 | 5,987 |
| fastapi + pydantic v2 | 256 | 45.48 | 188.08 | 4,951 | 4,951 |
| fastapi + stdlib json | 256 | 43.60 | 208.62 | 4,963 | 4,963 |
| fastapi + ujson | 256 | 43.39 | 190.07 | 5,199 | 5,199 |
| spring boot + hikaricp | 256 | 18.47 | 65.34 | **12,467** | 12,467 |

## GET /queries?n=20

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 63.80 | 131.24 | 967 | 19,338 |
| fastapi + msgspec | 64 | 53.35 | 130.05 | **1,060** | 21,199 |
| fastapi + pydantic v2 | 64 | 69.64 | 136.00 | 903 | 18,053 |
| fastapi + stdlib json | 64 | 73.66 | 167.40 | 805 | 16,098 |
| fastapi + ujson | 64 | 62.73 | 147.60 | 931 | 18,612 |
| spring boot + hikaricp | 64 | 75.79 | 143.73 | 810 | 16,195 |
| litestar + msgspec | 256 | 238.08 | 547.67 | **1,060** | 21,207 |
| fastapi + msgspec | 256 | 257.13 | 599.14 | 979 | 19,579 |
| fastapi + pydantic v2 | 256 | 271.53 | 688.25 | 920 | 18,392 |
| fastapi + stdlib json | 256 | 322.56 | 806.42 | 779 | 15,580 |
| fastapi + ujson | 256 | 253.03 | 633.01 | 1,001 | 20,024 |
| spring boot + hikaricp | 256 | 317.11 | 675.51 | 804 | 16,086 |

## GET /items?limit=100

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 26.88 | 60.06 | 2,227 | 2,227 |
| fastapi + msgspec | 64 | 24.39 | 81.51 | 2,292 | 2,292 |
| fastapi + pydantic v2 | 64 | 43.95 | 122.19 | 1,341 | 1,341 |
| fastapi + stdlib json | 64 | 40.54 | 101.41 | 1,477 | 1,477 |
| fastapi + ujson | 64 | 32.76 | 86.17 | 1,788 | 1,788 |
| spring boot + hikaricp | 64 | 16.59 | 45.61 | **3,550** | 3,550 |
| litestar + msgspec | 256 | 92.84 | 574.73 | 2,114 | 2,114 |
| fastapi + msgspec | 256 | 95.29 | 571.90 | 2,137 | 2,137 |
| fastapi + pydantic v2 | 256 | 55.01 | 1401.67 | 1,220 | 1,220 |
| fastapi + stdlib json | 256 | 47.43 | 1248.60 | 1,441 | 1,441 |
| fastapi + ujson | 256 | 40.14 | 917.39 | 1,801 | 1,801 |
| spring boot + hikaricp | 256 | 63.66 | 218.65 | **3,767** | 3,767 |

## POST /items

| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |
|---|---|---|---|---|---|
| litestar + msgspec | 64 | 13.35 | 30.33 | 4,496 | 4,496 |
| fastapi + msgspec | 64 | 14.38 | 31.91 | 4,189 | 4,189 |
| fastapi + pydantic v2 | 64 | 17.77 | 35.83 | 3,399 | 3,399 |
| fastapi + stdlib json | 64 | 17.34 | 36.92 | 3,456 | 3,456 |
| fastapi + ujson | 64 | 14.20 | 33.34 | 4,169 | 4,169 |
| spring boot + hikaricp | 64 | 5.24 | 17.90 | **10,758** | 10,758 |
| litestar + msgspec | 256 | 55.90 | 182.30 | 4,161 | 4,161 |
| fastapi + msgspec | 256 | 60.60 | 209.31 | 3,840 | 3,840 |
| fastapi + pydantic v2 | 256 | 70.31 | 241.53 | 3,313 | 3,313 |
| fastapi + stdlib json | 256 | 64.09 | 223.84 | 3,579 | 3,579 |
| fastapi + ujson | 256 | 56.22 | 197.01 | 4,051 | 4,051 |
| spring boot + hikaricp | 256 | 23.48 | 131.57 | **8,859** | 8,859 |

## Summary: req/s relative to the fastest Python stack (litestar + msgspec)

| Endpoint | Users | litestar + msgspec | fastapi + msgspec | fastapi + pydantic v2 | fastapi + stdlib json | fastapi + ujson | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|
| GET /json | 64 | 1.00x | 0.90x | 0.87x | 0.85x | 0.93x | 2.80x |
| GET /json | 256 | 1.00x | 0.79x | 0.78x | 0.77x | 0.84x | 2.62x |
| GET /db (1 query) | 64 | 1.00x | 0.99x | 0.82x | 0.76x | 0.86x | 2.49x |
| GET /db (1 query) | 256 | 1.00x | 0.98x | 0.81x | 0.81x | 0.85x | 2.03x |
| GET /queries?n=20 | 64 | 1.00x | 1.10x | 0.93x | 0.83x | 0.96x | 0.84x |
| GET /queries?n=20 | 256 | 1.00x | 0.92x | 0.87x | 0.73x | 0.94x | 0.76x |
| GET /items?limit=100 | 64 | 1.00x | 1.03x | 0.60x | 0.66x | 0.80x | 1.59x |
| GET /items?limit=100 | 256 | 1.00x | 1.01x | 0.58x | 0.68x | 0.85x | 1.78x |
| POST /items | 64 | 1.00x | 0.93x | 0.76x | 0.77x | 0.93x | 2.39x |
| POST /items | 256 | 1.00x | 0.92x | 0.80x | 0.86x | 0.97x | 2.13x |

## Per-round req/s (run-to-run noise)

| Endpoint | Users | litestar + msgspec | fastapi + msgspec | fastapi + pydantic v2 | fastapi + stdlib json | fastapi + ujson | spring boot + hikaricp |
|---|---|---|---|---|---|---|---|
| GET /json | 64 | 15,894, 15,704, 16,360 | 13,810, 14,791, 14,380 | 13,750, 13,026, 14,023 | 12,741, 13,588, 14,210 | 14,770, 15,004, 14,187 | 43,394, 44,528, 46,794 |
| GET /json | 256 | 16,490, 17,643, 17,213 | 13,969, 13,576, 13,099 | 13,454, 13,923, 13,200 | 13,175, 13,118, 13,513 | 14,488, 13,485, 14,617 | 49,720, 41,509, 45,093 |
| GET /db (1 query) | 64 | 6,072, 5,977, 6,522 | 5,722, 5,999, 6,682 | 5,566, 4,970, 4,978 | 4,917, 4,585, 4,530 | 5,244, 5,027, 5,208 | 15,972, 14,892, 15,142 |
| GET /db (1 query) | 256 | 5,898, 6,127, 6,239 | 5,480, 6,172, 5,987 | 5,026, 4,892, 4,951 | 4,610, 5,120, 4,963 | 5,212, 4,950, 5,199 | 12,467, 12,552, 11,614 |
| GET /queries?n=20 | 64 | 1,000, 915, 967 | 1,116, 1,044, 1,060 | 912, 903, 894 | 805, 915, 787 | 931, 978, 845 | 939, 785, 810 |
| GET /queries?n=20 | 256 | 1,120, 1,060, 1,021 | 1,036, 979, 899 | 887, 920, 1,032 | 779, 807, 727 | 898, 1,090, 1,001 | 796, 804, 882 |
| GET /items?limit=100 | 64 | 2,227, 2,234, 2,174 | 2,123, 2,308, 2,292 | 1,341, 1,342, 1,286 | 1,429, 1,477, 1,523 | 1,788, 1,988, 1,782 | 3,344, 3,582, 3,550 |
| GET /items?limit=100 | 256 | 2,114, 2,200, 1,983 | 2,222, 2,043, 2,137 | 1,220, 1,270, 1,209 | 1,436, 1,441, 1,526 | 1,731, 1,801, 1,814 | 3,571, 3,767, 3,912 |
| POST /items | 64 | 4,133, 4,603, 4,496 | 4,189, 4,249, 4,142 | 3,521, 3,399, 3,339 | 3,628, 3,408, 3,456 | 4,111, 4,259, 4,169 | 10,758, 10,720, 10,917 |
| POST /items | 256 | 4,042, 4,161, 4,423 | 3,781, 3,840, 3,991 | 3,287, 3,792, 3,313 | 3,320, 3,867, 3,579 | 4,217, 4,051, 3,804 | 8,859, 8,808, 9,417 |

All responses 2xx.

## Environment

- Python: `3.15.0 free-threading build (main, Oct  9 2026, 15:24:59) [Clang 22.1.3 ]` (GIL enabled: False)
- Java: `openjdk version "25.0.4.1" 2026-08-18`, JVM opts `-XX:+UseParallelGC -Xms1g -Xmx1g -XX:+AlwaysPreTouch`, virtual threads: True
- PostgreSQL: 18.4
- Kernel: 6.18.44-fc-v114, 4 vCPU; load generator: oha 1.16.0
- Server CPUs `0,1`, PostgreSQL CPUs `2`, oha CPUs `3`; 32 PostgreSQL connections in total per stack
- granian flags: `--interface asgi --loop uvloop --http 1 --no-ws --workers 2 --runtime-mode mt --runtime-threads 2 --task-impl rust --log-level warning --no-access-log`
- 3 x 15s rounds after 5s warmup (30s for the JVM)
- Python packages: litestar 2.24.0, msgspec 0.22.0, fastapi 0.143.0, starlette 1.7.0, pydantic 2.14.0, pydantic-core 2.50.0, ujson 6.0.0, granian 2.8.4, uvloop 0.23.0, asyncpg 0.32.0
- Java stack: Spring Boot 4.1.1 (Spring 7.0.9, Tomcat 11.0.24, Jackson 3.1.5), HikariCP 7.1.0, pgjdbc 42.7.14, Hibernate Validator 9.1.3
