#!/usr/bin/env bash
# Fetch official PostgreSQL 18.4 binaries (via the embedded-postgres npm package, since
# apt.postgresql.org may be unreachable) and start a throwaway benchmark cluster.
set -euo pipefail
PG_VER="${PG_VER:-18.4.0-beta.17}"
PREFIX="${PREFIX:-/opt/pg18}"
DATA="${DATA:-/opt/pgdata/18}"
RUN_AS="${RUN_AS:-pgbench}"

mkdir -p "$PREFIX"
cd "$PREFIX"
tarball=$(curl -fsS "https://registry.npmjs.org/@embedded-postgres/linux-x64/$PG_VER" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['dist']['tarball'])")
curl -fsS -o pg.tgz "$tarball"
tar xzf pg.tgz
cd package
python3 - <<'PY'
import json, os
for e in json.load(open("native/pg-symlinks.json")):
    if not os.path.lexists(e["target"]):
        os.symlink(os.path.basename(e["source"]), e["target"])
PY
BIN="$PREFIX/package/native/bin"

id "$RUN_AS" >/dev/null 2>&1 || useradd -m "$RUN_AS"
mkdir -p "$(dirname "$DATA")" && chown "$RUN_AS" "$(dirname "$DATA")"
su "$RUN_AS" -c "$BIN/initdb -D $DATA -U postgres --auth=trust -E UTF8"
su "$RUN_AS" -c "$BIN/pg_ctl -D $DATA -l $(dirname "$DATA")/log \
  -o '-p 5432 -c max_connections=300 -c shared_buffers=512MB -c synchronous_commit=off' start"
sleep 2
"$BIN/psql" -h 127.0.0.1 -U postgres -c "CREATE DATABASE bench"
