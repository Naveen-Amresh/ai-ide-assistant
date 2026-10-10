"""FastAPI + stdlib json + asyncpg."""

import json
from functools import partial

from apps._fastapi_raw import build

app = build("fastapi-json", partial(json.dumps, separators=(",", ":")), json.loads)
