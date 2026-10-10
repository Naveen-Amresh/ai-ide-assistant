"""Render results/results.json into results/RESULTS.md."""

import json
import sys
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "results" / "results.json")
data = json.loads(src.read_text())
meta, results = data["meta"], data["results"]
apps = list(results)
endpoints = list(next(iter(results.values())))
baseline = "fastapi + pydantic v2"

lines = ["# Results", "", "## Throughput (req/s, median of rounds; higher is better)", ""]
lines.append("| Endpoint | " + " | ".join(apps) + " |")
lines.append("|---" * (len(apps) + 1) + "|")
for ep in endpoints:
    best = max(results[a][ep]["rps"] for a in apps)
    cells = []
    for a in apps:
        rps = results[a][ep]["rps"]
        rel = rps / results[baseline][ep]["rps"]
        cell = f"{rps:,.0f} ({rel:.2f}x)"
        cells.append(f"**{cell}**" if rps == best else cell)
    lines.append(f"| {ep} | " + " | ".join(cells) + " |")
lines += ["", f"Ratios are relative to `{baseline}`. Best per row in bold.", ""]

lines += ["## Latency p50 / p99 (ms; lower is better)", ""]
lines.append("| Endpoint | " + " | ".join(apps) + " |")
lines.append("|---" * (len(apps) + 1) + "|")
for ep in endpoints:
    cells = [f"{results[a][ep]['p50_ms']:.2f} / {results[a][ep]['p99_ms']:.2f}" for a in apps]
    lines.append(f"| {ep} | " + " | ".join(cells) + " |")

lines += ["", "## Per-round req/s (run-to-run noise)", ""]
lines.append("| Endpoint | " + " | ".join(apps) + " |")
lines.append("|---" * (len(apps) + 1) + "|")
for ep in endpoints:
    cells = [", ".join(f"{r:,}" for r in results[a][ep]["rps_runs"]) for a in apps]
    lines.append(f"| {ep} | " + " | ".join(cells) + " |")

failed = [(a, ep) for a in apps for ep in endpoints if results[a][ep]["ok_ratio"] < 0.999]
lines += ["", "All responses 2xx." if not failed else f"Non-2xx responses in: {failed}", ""]

s = meta["settings"]
lines += [
    "## Environment", "",
    f"- Python: `{meta['python']}` (GIL enabled: {meta['gil_enabled']})",
    f"- PostgreSQL: {meta['postgres']}",
    f"- Kernel: {meta['kernel']}, {meta['cpus']} vCPU; load generator: {meta['oha']}",
    f"- granian: {s['workers']} workers (threads on free-threaded Python), ASGI, uvloop, "
    f"server CPUs `{s['server_cpus']}`, PostgreSQL CPUs `{s['pg_cpus']}`, oha CPUs `{s['load_cpus']}`",
    f"- {s['connections']} connections, {s['rounds']} x {s['duration']}s rounds after {s['warmup']}s warmup",
    "- Packages: " + ", ".join(f"{k} {v}" for k, v in meta["packages"].items()),
    "",
]
out = src.parent / "RESULTS.md"
out.write_text("\n".join(lines))
print(out.read_text())
