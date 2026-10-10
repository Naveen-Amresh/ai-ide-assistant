"""Short sweep over granian performance flags to pick the fastest configuration.

Total DB connections are held at TOTAL_POOL regardless of worker count, so a
config cannot "win" just by opening more PostgreSQL connections.
"""

import argparse
import itertools
import json
import os
import signal
import subprocess
from pathlib import Path

from run_bench import ENDPOINTS, GRANIAN, oha, pin_postgres, wait_ready

ROOT = Path(__file__).parent
TOTAL_POOL = 32


def granian_cmd(target: str, port: int, workers: int, mode: str, rt_threads: int, task: str,
                backpressure: int | None) -> list[str]:
    cmd = [GRANIAN, "--interface", "asgi", "--loop", "uvloop", "--http", "1", "--no-ws",
           "--workers", str(workers), "--runtime-mode", mode, "--runtime-threads", str(rt_threads),
           "--task-impl", task, "--port", str(port), "--log-level", "warning", "--no-access-log"]
    if backpressure:
        cmd += ["--backpressure", str(backpressure)]
    return cmd + [target]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apps", default="apps.litestar_msgspec:app,apps.fastapi_pydantic:app")
    ap.add_argument("--endpoints", default="GET /json,GET /db (1 query),GET /items?limit=100")
    ap.add_argument("--duration", type=int, default=5)
    ap.add_argument("--connections", type=int, default=64)
    ap.add_argument("--server-cpus", default="0,1")
    ap.add_argument("--load-cpus", default="3")
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--out", default=str(ROOT / "results" / "granian_tuning.json"))
    args = ap.parse_args()

    pin_postgres("2")
    grid = [
        # (workers, runtime-mode, runtime-threads, task-impl, backpressure)
        *[(w, m, t, ti, None) for w, (m, t), ti in itertools.product(
            (1, 2, 4), (("st", 1), ("mt", 2)), ("asyncio", "rust"))],
        (2, "st", 1, "rust", 64), (2, "st", 1, "rust", 256),
    ]
    rows = []
    for target in args.apps.split(","):
        for workers, mode, rt, task, bp in grid:
            env = os.environ | {"BENCH_POOL_SIZE": str(TOTAL_POOL // workers)}
            proc = subprocess.Popen(
                ["taskset", "-c", args.server_cpus, *granian_cmd(target, args.port, workers, mode, rt, task, bp)],
                cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                wait_ready(args.port)
                row = {"app": target, "workers": workers, "mode": mode, "rt_threads": rt,
                       "task_impl": task, "backpressure": bp}
                for ep in args.endpoints.split(","):
                    oha(ENDPOINTS[ep], args.port, 2, args.connections, args.load_cpus)
                    r = oha(ENDPOINTS[ep], args.port, args.duration, args.connections, args.load_cpus)
                    row[ep] = round(r["rps"]) if r["ok_ratio"] > 0.999 else 0
                rows.append(row)
                print(json.dumps(row), flush=True)
            except Exception as exc:  # a config that fails to start just scores 0
                print(f"FAILED {target} {workers} {mode} {rt} {task} {bp}: {exc}", flush=True)
            finally:
                os.killpg(proc.pid, signal.SIGINT)
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
    Path(args.out).write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
