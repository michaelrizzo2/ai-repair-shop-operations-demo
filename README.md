# Repair desk

From a repair request to a reviewed next step. A portfolio starter by Michael Rizzo.

**Status: runnable local deterministic demo with synthetic data. Live API adapters and public hosting are not implemented.**

[Portfolio](https://michaelrizzo2.github.io/#projects) · [Source](https://github.com/michaelrizzo2/ai-repair-shop-operations-demo)

## Implemented behavior

The first complete workflow uses a structured preset intake, compatible synthetic inventory, integer-cent pricing, a response draft and session-bound approval. The SSE endpoint replays completed workflow events; it is not live model reasoning. All records, slots and prices are fictional. Sessions expire after 15 minutes and accept at most 30 workflows; a 500-session cap bounds in-memory state. Run a single server worker. There are no external connectors or model calls in this milestone.

## Run locally

Python 3.11 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8011
```

Open http://127.0.0.1:8011. API documentation is at `/docs`; `/api/health` reports the active mode. Production dependencies alone are in `requirements.txt`. No credentials are needed or loaded for this deterministic milestone.

## Architecture

Browser → FastAPI validation → deterministic workflow/ranking/backtest → inspectable structured response.

The application uses a small flat file layout: `app.py` contains the typed request schema and workflow; `ui.html`, `styles.css` and `ui.js` implement the interface; `test_app.py` exercises the important boundaries. This keeps the initial case study easy to clone and run.

## Verification and limitations

Run the tests above. They verify input rejection, domain calculations and the specific decision boundaries, not model accuracy. Synthetic scenarios demonstrate behavior but do not establish real-world business impact or trading performance. No private customer records or credentials belong in this repository.

## Next milestone

Add a TypeSafe Choice adapter for routing plus independent Noul checks for missing information. Validate on labeled preset and adversarial cases. Add sandbox connector contracts and deliberate public-hosting limits before any real free-text model path.

TypeSafe integration design follows the current [API](https://docs.typesafe.ai/api), [Python SDK](https://docs.typesafe.ai/sdk/python) and [composite scoring](https://docs.typesafe.ai/patterns/composite-scoring) documentation. Planned model behavior is not represented as implemented inference.
