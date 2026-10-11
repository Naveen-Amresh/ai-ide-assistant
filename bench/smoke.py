"""Start each named stack via run_bench.server_cmd, check every endpoint, stop it cleanly."""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

import run_bench as rb

PORT = 8800
GOOD = json.dumps({"name": "x", "price": 1.5, "quantity": 2, "tags": ["a"]}).encode()
BAD = json.dumps({"name": "", "price": -1, "quantity": 2}).encode()


def call(path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=body,
                                 headers={"content-type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def port_free() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1)
        return False
    except Exception:
        return True


args = rb.argparse.Namespace(workers=2, runtime_mode="mt", runtime_threads=2, task_impl="rust",
                             backpressure=None, total_pool=32, port=PORT, java_opts="",
                             java_virtual_threads=True)
rb.pin_postgres("2")
for name in sys.argv[1:]:
    assert port_free(), f"port {PORT} busy before {name}"
    cmd, env = rb.server_cmd(name, args)
    proc = subprocess.Popen(cmd, cwd=rb.ROOT, env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        rb.wait_ready(PORT)
        checks = {
            "json": call("/json") == (200, b'{"message":"Hello, World!"}'),
            "db x30": all(call("/db")[0] == 200 for _ in range(30)),
            "queries": (lambda r: r[0] == 200 and len(json.loads(r[1])) == 20)(call("/queries?n=20")),
            "items": (lambda r: r[0] == 200 and len(json.loads(r[1])) == 100)(call("/items?limit=100")),
            "post 201": call("/items", GOOD)[0] == 201,
            "bad 4xx": 400 <= call("/items", BAD)[0] < 500,
        }
        print(f"{name:34} " + "  ".join(f"{k}:{'ok' if v else 'FAIL'}" for k, v in checks.items()), flush=True)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        for _ in range(40):
            if port_free():
                break
            time.sleep(0.25)
