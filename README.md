# Repair shop operations

[Portfolio](https://michaelrizzo2.github.io/#projects) · [Try the case study](https://michaelrizzo2.github.io/#demo-repair)

A working TypeSafe integration for bounded **fictional** repair requests. `typesafe_adapter.py` validates Choice/Noul answers from pinned `jev-1.13.0`; code owns catalog lookup, integer-cent prices and human approval. `live_service.py` stores expiring sessions and budget counters in SQLite outside the checkout. Credentials remain server-side. Funnel now publishes only the bounded repair service on HTTPS port 10000. Recorded model judgments and explicit offline examples remain available when live access fails.

The server limits inference to 5 calls per 15-minute session, 90 global calls/day, 120,000 reserved/used input tokens/day, two concurrent calls, 600 characters and 8 KiB requests. Failed calls conservatively retain a 6,000-token reservation. It rejects foreign origins, malformed provider output and mismatched, stale or repeated approvals. The API key is read from `TYPESAFE_API_KEY` or the owner’s private `~/.config/typesafe-ai/api-key`; never commit it. CORS is a browser boundary, not authentication. Global budgets remain effective when anonymous visitors create new sessions.

## Measured synthetic evaluation

48 hand-labeled requests were frozen before successful inference: 6 calibration, 42 holdout; thresholds fixed before inference and not tuned on the holdout. 42/42 workflow outcomes matched labels; keyword baseline 36/42. Zero incorrect approval-required outcomes in this small sample. Median API latency 189.82 ms; p95 257.75 ms; 34,609 input tokens; estimated provider cost $0.001453578 across 48 calls at $0.042/million input tokens, excluding hosting/gateway costs. Inspect `evaluation-cases.json`, `evaluation-results.json`, and `evaluate_live.py`. This is a workflow-quality benchmark, not customer savings, production accuracy or a safety guarantee. The initial integration check received HTTP 422 because Noul criteria used an incorrect shape; it was corrected before deployment, with frozen labels and thresholds unchanged.

## Live service locally

Install production dependencies, then run `.venv/bin/python -m uvicorn live_service:app --host 127.0.0.1 --port 8021`. `/api/health` exposes configuration status without secrets. POST `/api/session`, then `/api/live/run` with the ephemeral session token and fictional text. Only `/api/live/approve` can approve the current proposal. All bookings remain fictional. `/api/metrics` contains daily aggregates, not user text. Access logging is disabled in the installed user service.

A local user service named `portfolio-ai-demo.service` runs this backend persistently. The public gateway is enabled on port 10000 to localhost:8021. Public-relay inference and policy checks passed; both relay certificates validate. Independent phone and published-page browser access still need verification because Edge reports a client-side block. Other Tailscale routes remain private. See `DEPLOYMENT.md` for exact steps.

## Limits

No physical diagnosis, real inventory reservation, real customer data or business-system execution. Small synthetic coverage, anonymous budget-limited access, a single host with no uptime SLA and model/provider dependence. Request text goes to TypeSafe; this demo persists a hash, not raw request text. SQLite records proposal results and telemetry; no claim is made about provider retention policies.

## Run and verify

Python 3.11+:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8011
```

Open http://127.0.0.1:8011. The shared browser workspace uses published evidence assets; enhanced Python APIs expose independent reproducible calculations. All four browser modes are included to make comparison easy; each repository’s own Python implementation is its named project. Repair live mode additionally needs the separately configured backend on 8021. No credentials are bundled in browser files.

14 Python tests pass for this project. Portfolio tests and 45 enhanced Python/browser parity combinations validate the shared outputs. See `VALIDATION.md`.
