"""Benchmark runner: starts each app, drives it with oha, writes results/results.json.

CPU layout (4 vCPU box): server on SERVER_CPUS, PostgreSQL on PG_CPUS, load generator on
LOAD_CPUS, so the three never fight over the same cores. Every stack gets the same total
number of PostgreSQL connections (--total-pool).
"""

import argparse
import json
import os
import platform
import signal
import statistics
import subprocess
import sys
import time
import urllib.request
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).parent
PY = sys.executable
GRANIAN = str(Path(PY).parent / "granian")
OHA = os.environ.get("OHA", str(Path.home() / ".cargo/bin/oha"))
JAVA = os.environ.get("JAVA", "/usr/lib/jvm/java-25-openjdk-amd64/bin/java")
SPRING_JAR = ROOT / "spring" / "target" / "spring-bench.jar"

APPS = {
    "litestar + msgspec": "apps.litestar_msgspec:app",
    "fastapi + msgspec": "apps.fastapi_msgspec:app",
    "fastapi + pydantic v2": "apps.fastapi_pydantic:app",
    "fastapi + stdlib json": "apps.fastapi_json:app",
    "fastapi + ujson": "apps.fastapi_ujson:app",
    "spring boot + hikaricp": "java",
}

POST_BODY = json.dumps({"name": "bench-item", "price": 19.99, "quantity": 3, "tags": ["a", "b", "c"]})
ENDPOINTS = {
    "GET /json": ["/json"],
    "GET /db (1 query)": ["/db"],
    "GET /queries?n=20": ["/queries?n=20"],
    "GET /items?limit=100": ["/items?limit=100"],
    "POST /items": ["/items", "-m", "POST", "-H", "content-type: application/json", "-d", POST_BODY],
}
# DB statements per request, to turn req/s into DB transactions/s.
QUERIES_PER_REQUEST = {"GET /json": 0, "GET /db (1 query)": 1, "GET /queries?n=20": 20,
                       "GET /items?limit=100": 1, "POST /items": 1}


def pin_postgres(cpus: str) -> None:
    """Ensure PostgreSQL is up (containers may kill it while idle), then pin it to `cpus`."""
    if subprocess.run(["pg_isready", "-h", "127.0.0.1", "-q"]).returncode != 0:
        subprocess.run([str(ROOT / "start_postgres.sh")], check=True)
    pids = subprocess.run(["pgrep", "-x", "postgres"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        subprocess.run(["taskset", "-a", "-p", "-c", cpus, pid], capture_output=True)


def wait_ready(port: int, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1).read()
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("server did not become ready")


def oha(url_and_args: list[str], port: int, duration: int, conns: int, cpus: str) -> dict:
    path, *extra = url_and_args
    cmd = ["taskset", "-c", cpus, OHA, f"http://127.0.0.1:{port}{path}", "-z", f"{duration}s",
           "-c", str(conns), "--no-tui", "--output-format", "json", *extra]
    out = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    s, lat = out["summary"], out["latencyPercentiles"]
    codes = out.get("statusCodeDistribution", {})
    ok = sum(v for k, v in codes.items() if k.startswith("2"))
    total = sum(codes.values()) or 1
    return {
        "rps": s["requestsPerSec"],
        "p50_ms": lat["p50"] * 1000,
        "p99_ms": lat["p99"] * 1000,
        "ok_ratio": ok / total,
    }


def granian_flags(args) -> list[str]:
    flags = ["--interface", "asgi", "--loop", "uvloop", "--http", "1", "--no-ws",
             "--workers", str(args.workers), "--runtime-mode", args.runtime_mode,
             "--runtime-threads", str(args.runtime_threads), "--task-impl", args.task_impl,
             "--log-level", "warning", "--no-access-log"]
    if args.backpressure:
        flags += ["--backpressure", str(args.backpressure)]
    return flags


def server_cmd(target: str, args) -> tuple[list[str], dict]:
    env = dict(os.environ)
    if target == "java":
        env |= {"BENCH_PORT": str(args.port), "BENCH_POOL_SIZE": str(args.total_pool),
                "BENCH_VIRTUAL_THREADS": str(args.java_virtual_threads).lower()}
        return [JAVA, *args.java_opts.split(), "-jar", str(SPRING_JAR)], env
    env["BENCH_POOL_SIZE"] = str(max(1, args.total_pool // args.workers))
    return [GRANIAN, *granian_flags(args), "--port", str(args.port), target], env


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", default=",".join(APPS), help="comma-separated names from APPS")
    ap.add_argument("--duration", type=int, default=15)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--java-warmup", type=int, default=30, help="JIT needs longer warmup")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--connections", default="64,256", help="comma-separated concurrency levels")
    ap.add_argument("--total-pool", type=int, default=32)
    # granian (defaults = winner of tune_granian.py)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--runtime-mode", default="st")
    ap.add_argument("--runtime-threads", type=int, default=1)
    ap.add_argument("--task-impl", default="asyncio")
    ap.add_argument("--backpressure", type=int, default=None)
    # JVM (defaults = winner of tune_spring.py)
    ap.add_argument("--java-opts", default="-XX:+UseParallelGC -Xms1g -Xmx1g -XX:+AlwaysPreTouch")
    ap.add_argument("--java-virtual-threads", type=lambda s: s.lower() == "true", default=True)
    ap.add_argument("--server-cpus", default="0,1")
    ap.add_argument("--pg-cpus", default="2")
    ap.add_argument("--load-cpus", default="3")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()
    levels = [int(c) for c in args.connections.split(",")]

    pin_postgres(args.pg_cpus)
    results: dict[str, dict[str, dict[str, dict]]] = {}
    for name in args.apps.split(","):
        target = APPS[name]
        subprocess.run([PY, str(ROOT / "seed.py")], check=True, cwd=ROOT, capture_output=True)
        cmd, env = server_cmd(target, args)
        proc = subprocess.Popen(["taskset", "-c", args.server_cpus, *cmd], cwd=ROOT, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        warmup = args.java_warmup if target == "java" else args.warmup
        try:
            wait_ready(args.port)
            results[name] = {}
            for ep, spec in ENDPOINTS.items():
                results[name][ep] = {}
                for conns in levels:
                    oha(spec, args.port, warmup, conns, args.load_cpus)
                    runs = [oha(spec, args.port, args.duration, conns, args.load_cpus)
                            for _ in range(args.rounds)]
                    best = {k: statistics.median(r[k] for r in runs) for k in runs[0]}
                    best["rps_runs"] = [round(r["rps"]) for r in runs]
                    best["db_tps"] = best["rps"] * QUERIES_PER_REQUEST[ep]
                    results[name][ep][str(conns)] = best
                    print(f"{name:24} {ep:22} c={conns:<4} {best['rps']:>9.0f} req/s"
                          f"  p50 {best['p50_ms']:7.2f}  p99 {best['p99_ms']:7.2f} ms"
                          f"  ok {best['ok_ratio']:.3f}", flush=True)
        finally:
            os.killpg(proc.pid, signal.SIGINT if target != "java" else signal.SIGTERM)
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)

    pg_version = subprocess.run(
        ["psql", "-h", "127.0.0.1", "-U", "postgres", "-tAc", "SHOW server_version"],
        capture_output=True, text=True).stdout.strip()
    java_version = subprocess.run([JAVA, "-version"], capture_output=True, text=True).stderr
    java_version = next((l for l in java_version.splitlines() if "version" in l), "").strip()
    meta = {
        "python": sys.version.replace("\n", " "),
        "gil_enabled": sys._is_gil_enabled(),
        "postgres": pg_version,
        "java": java_version,
        "kernel": platform.release(),
        "cpus": os.cpu_count(),
        "oha": subprocess.run([OHA, "--version"], capture_output=True, text=True).stdout.strip(),
        "granian_flags": " ".join(granian_flags(args)),
        "packages": {p: version(p) for p in [
            "litestar", "msgspec", "fastapi", "starlette", "pydantic", "pydantic-core",
            "ujson", "granian", "uvloop", "asyncpg"]},
        "java_stack": "Spring Boot 4.1.1 (Spring 7.0.9, Tomcat 11.0.24, Jackson 3.1.5), "
                      "HikariCP 7.1.0, pgjdbc 42.7.14, Hibernate Validator 9.1.3",
        "settings": vars(args),
    }
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    print(f"wrote {out / 'results.json'}")


if __name__ == "__main__":
    main()
