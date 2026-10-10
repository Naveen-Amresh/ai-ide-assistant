"""Short sweep over JVM / Spring threading options to pick the fastest configuration."""

import argparse
import json
import os
import signal
import subprocess
from pathlib import Path

from run_bench import ENDPOINTS, JAVA, SPRING_JAR, oha, pin_postgres, wait_ready

ROOT = Path(__file__).parent
BASE = "-Xms1g -Xmx1g -XX:+AlwaysPreTouch"
GRID = [
    # (label, JVM opts, virtual threads)
    ("parallel+coh vt", f"-XX:+UseParallelGC -XX:+UseCompactObjectHeaders {BASE}", True),
    ("parallel+coh platform", f"-XX:+UseParallelGC -XX:+UseCompactObjectHeaders {BASE}", False),
    ("parallel vt", f"-XX:+UseParallelGC {BASE}", True),
    ("g1+coh vt", f"-XX:+UseG1GC -XX:+UseCompactObjectHeaders {BASE}", True),
    ("zgc+coh vt", f"-XX:+UseZGC -XX:+UseCompactObjectHeaders {BASE}", True),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoints", default="GET /json,GET /db (1 query),GET /items?limit=100")
    ap.add_argument("--warmup", type=int, default=15)
    ap.add_argument("--duration", type=int, default=5)
    ap.add_argument("--connections", type=int, default=64)
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--out", default=str(ROOT / "results" / "spring_tuning.json"))
    args = ap.parse_args()

    pin_postgres("2")
    rows = []
    for label, opts, vt in GRID:
        env = os.environ | {"BENCH_PORT": str(args.port), "BENCH_POOL_SIZE": "32",
                            "BENCH_VIRTUAL_THREADS": str(vt).lower()}
        proc = subprocess.Popen(["taskset", "-c", "0,1", JAVA, *opts.split(), "-jar", str(SPRING_JAR)],
                                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            wait_ready(args.port)
            row = {"config": label, "opts": opts, "virtual_threads": vt}
            for ep in args.endpoints.split(","):
                oha(ENDPOINTS[ep], args.port, args.warmup, args.connections, "3")
                r = oha(ENDPOINTS[ep], args.port, args.duration, args.connections, "3")
                row[ep] = round(r["rps"]) if r["ok_ratio"] > 0.999 else 0
            rows.append(row)
            print(json.dumps(row), flush=True)
        finally:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
    Path(args.out).write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
