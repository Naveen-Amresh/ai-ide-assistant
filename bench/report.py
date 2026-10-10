"""Render results/results.json into results/RESULTS.md."""

import json
import sys
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "results" / "results.json")
data = json.loads(src.read_text())
meta, results = data["meta"], data["results"]
apps = list(results)
endpoints = list(next(iter(results.values())))
levels = list(next(iter(next(iter(results.values())).values())))


def fmt(n: float) -> str:
    return f"{n:,.0f}"


lines = ["# Results", ""]
lines += ["Users = concurrent keep-alive connections. Req/s = HTTP throughput. "
          "DB TPS = database statements per second (req/s x statements per request). "
          "Values are medians of the rounds; best req/s per endpoint and user count in bold.", ""]

for ep in endpoints:
    lines += [f"## {ep}", "", "| Framework | Users | p50 (ms) | p99 (ms) | Req/s | DB TPS |",
              "|---|---|---|---|---|---|"]
    for conns in levels:
        best = max(results[a][ep][conns]["rps"] for a in apps)
        for a in apps:
            r = results[a][ep][conns]
            rps = f"**{fmt(r['rps'])}**" if r["rps"] == best else fmt(r["rps"])
            tps = fmt(r["db_tps"]) if r["db_tps"] else "0 (no DB)"
            lines.append(f"| {a} | {conns} | {r['p50_ms']:.2f} | {r['p99_ms']:.2f} | {rps} | {tps} |")
    lines.append("")

lines += ["## Summary: req/s relative to the fastest Python stack (litestar + msgspec)", "",
          "| Endpoint | Users | " + " | ".join(apps) + " |", "|---" * (len(apps) + 2) + "|"]
for ep in endpoints:
    for conns in levels:
        base = results["litestar + msgspec"][ep][conns]["rps"]
        cells = [f"{results[a][ep][conns]['rps'] / base:.2f}x" for a in apps]
        lines.append(f"| {ep} | {conns} | " + " | ".join(cells) + " |")

lines += ["", "## Per-round req/s (run-to-run noise)", "",
          "| Endpoint | Users | " + " | ".join(apps) + " |", "|---" * (len(apps) + 2) + "|"]
for ep in endpoints:
    for conns in levels:
        cells = [", ".join(f"{x:,}" for x in results[a][ep][conns]["rps_runs"]) for a in apps]
        lines.append(f"| {ep} | {conns} | " + " | ".join(cells) + " |")

failed = [(a, ep, c) for a in apps for ep in endpoints for c in levels
          if results[a][ep][c]["ok_ratio"] < 0.999]
lines += ["", "All responses 2xx." if not failed else f"Non-2xx responses in: {failed}", ""]

s = meta["settings"]
lines += [
    "## Environment", "",
    f"- Python: `{meta['python']}` (GIL enabled: {meta['gil_enabled']})",
    f"- Java: `{meta['java']}`, JVM opts `{s['java_opts']}`, virtual threads: {s['java_virtual_threads']}",
    f"- PostgreSQL: {meta['postgres']}",
    f"- Kernel: {meta['kernel']}, {meta['cpus']} vCPU; load generator: {meta['oha']}",
    f"- Server CPUs `{s['server_cpus']}`, PostgreSQL CPUs `{s['pg_cpus']}`, oha CPUs `{s['load_cpus']}`; "
    f"{s['total_pool']} PostgreSQL connections in total per stack",
    f"- granian flags: `{meta['granian_flags']}`",
    f"- {s['rounds']} x {s['duration']}s rounds after {s['warmup']}s warmup "
    f"({s['java_warmup']}s for the JVM)",
    "- Python packages: " + ", ".join(f"{k} {v}" for k, v in meta["packages"].items()),
    f"- Java stack: {meta['java_stack']}",
    "",
]
out = src.parent / "RESULTS.md"
out.write_text("\n".join(lines))
print(out.read_text())
