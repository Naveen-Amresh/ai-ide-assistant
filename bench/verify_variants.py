"""Check json_agg / Polars / Spring variants return the same data as the msgspec baseline."""

import json
import os
import signal
import subprocess
import time
import urllib.request
from datetime import datetime

import run_bench as rb

PORT = 8801
VARIANTS = ["[gil] emmett55 + msgspec (rsgi)", "[gil] emmett55 + json_agg (rsgi)",
            "[gil] emmett55 + polars/adbc (rsgi)", "spring boot + hikaricp", "spring boot + json_agg"]


def norm(rows):
    for r in rows:
        r["created_at"] = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).isoformat()
    return rows


def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=30) as r:
        return r.headers.get("content-type"), json.loads(r.read())


args = rb.argparse.Namespace(workers=2, runtime_mode="mt", runtime_threads=2, task_impl="rust",
                             backpressure=None, total_pool=32, port=PORT,
                             java_opts="-XX:+UseParallelGC -Xmx512m", java_virtual_threads=True)
rb.pin_postgres("2")
subprocess.run([rb.PY, "seed.py"], check=True, cwd=rb.ROOT, capture_output=True)
baseline = None
for name in VARIANTS:
    cmd, env = rb.server_cmd(name, args)
    proc = subprocess.Popen(cmd, cwd=rb.ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        rb.wait_ready(PORT)
        pre = rb.APPS[name][3].get("path_prefix", "")
        ct, one = get(f"{pre}/db")
        _, items = get(f"{pre}/items?limit=100")
        _, export = get(f"{pre}/export?rows=10000")
        got = (sorted(one), norm(items), norm(export))
        if baseline is None:
            baseline = got
        same = got[0] == baseline[0] and got[1] == baseline[1] and got[2] == baseline[2]
        print(f"{name:38} content-type={ct:18} db keys ok={got[0] == baseline[0]} items={len(items)} "
              f"export={len(export)} identical_to_baseline={same}", flush=True)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        time.sleep(1)
