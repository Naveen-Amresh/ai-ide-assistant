"""Benchmark runner: starts each app under granian, drives it with oha, writes results.

CPU layout (4 vCPU box): server workers on SERVER_CPUS, PostgreSQL on PG_CPUS,
load generator on LOAD_CPUS, so the three never fight over the same cores.
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

APPS = {
    "litestar + msgspec": "apps.litestar_msgspec:app",
    "fastapi + pydantic v2": "apps.fastapi_pydantic:app",
    "fastapi + stdlib json": "apps.fastapi_json:app",
    "fastapi + ujson": "apps.fastapi_ujson:app",
}

POST_BODY = json.dumps({"name": "bench-item", "price": 19.99, "quantity": 3, "tags": ["a", "b", "c"]})
ENDPOINTS = {
    "GET /json": ["/json"],
    "GET /db (1 query)": ["/db"],
    "GET /queries?n=20": ["/queries?n=20"],
    "GET /items?limit=100": ["/items?limit=100"],
    "POST /items": ["/items", "-m", "POST", "-H", "content-type: application/json", "-d", POST_BODY],
}


def pin_postgres(cpus: str) -> None:
    pids = subprocess.run(["pgrep", "-x", "postgres"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        subprocess.run(["taskset", "-a", "-p", "-c", cpus, pid], capture_output=True)


def wait_ready(port: int, timeout: float = 30) -> None:
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--connections", type=int, default=64)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--server-cpus", default="0,1")
    ap.add_argument("--pg-cpus", default="2")
    ap.add_argument("--load-cpus", default="3")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    pin_postgres(args.pg_cpus)
    results: dict[str, dict[str, dict]] = {}
    for name, target in APPS.items():
        subprocess.run([PY, str(ROOT / "seed.py")], check=True, cwd=ROOT, capture_output=True)
        proc = subprocess.Popen(
            ["taskset", "-c", args.server_cpus, GRANIAN, "--interface", "asgi", "--loop", "uvloop",
             "--workers", str(args.workers), "--port", str(args.port), "--log-level", "warning",
             "--no-access-log", target],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            start_new_session=True,
        )
        try:
            wait_ready(args.port)
            results[name] = {}
            for ep, spec in ENDPOINTS.items():
                oha(spec, args.port, args.warmup, args.connections, args.load_cpus)
                runs = [oha(spec, args.port, args.duration, args.connections, args.load_cpus)
                        for _ in range(args.rounds)]
                best = {k: statistics.median(r[k] for r in runs) for k in runs[0]}
                best["rps_runs"] = [round(r["rps"]) for r in runs]
                results[name][ep] = best
                print(f"{name:24} {ep:22} {best['rps']:>10.0f} req/s  p50 {best['p50_ms']:6.2f} ms"
                      f"  p99 {best['p99_ms']:7.2f} ms  ok {best['ok_ratio']:.3f}", flush=True)
        finally:
            os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)

    pg_version = subprocess.run(
        ["psql", "-h", "127.0.0.1", "-U", "postgres", "-tAc", "SHOW server_version"],
        capture_output=True, text=True).stdout.strip()
    meta = {
        "python": sys.version.replace("\n", " "),
        "gil_enabled": sys._is_gil_enabled(),
        "postgres": pg_version,
        "kernel": platform.release(),
        "cpus": os.cpu_count(),
        "oha": subprocess.run([OHA, "--version"], capture_output=True, text=True).stdout.strip(),
        "packages": {p: version(p) for p in [
            "litestar", "msgspec", "fastapi", "starlette", "pydantic", "pydantic-core",
            "ujson", "granian", "uvloop", "asyncpg"]},
        "settings": vars(args),
    }
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    print(f"wrote {out / 'results.json'}")


if __name__ == "__main__":
    main()
