#!/usr/bin/env bash
# (Re)start the benchmark PostgreSQL cluster with throughput-oriented settings.
set -euo pipefail
BIN="${BIN:-/opt/pg18/package/native/bin}"
DATA="${DATA:-/opt/pgdata/18}"
RUN_AS="${RUN_AS:-pgbench}"
OPTS="-p 5432 -c max_connections=300 -c shared_buffers=1GB -c effective_cache_size=3GB \
-c work_mem=16MB -c synchronous_commit=off -c wal_buffers=64MB -c max_wal_size=8GB \
-c checkpoint_timeout=30min -c checkpoint_completion_target=0.9 -c random_page_cost=1.1 \
-c jit=off -c track_activities=off -c track_counts=on -c log_checkpoints=off"
if su "$RUN_AS" -c "$BIN/pg_ctl -D $DATA status" >/dev/null 2>&1; then
  su "$RUN_AS" -c "$BIN/pg_ctl -D $DATA -m fast stop"
fi
su "$RUN_AS" -c "$BIN/pg_ctl -D $DATA -l $(dirname "$DATA")/log -o '$OPTS' -w start"
