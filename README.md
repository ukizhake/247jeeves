# outlast.money

Retirement tax intelligence — Phase 1 rules-based simulator.

## Stack

| Layer | Tech |
|-------|------|
| Engine | Python, Pandas/NumPy, YAML rules |
| API | FastAPI, SQLite → PostgreSQL |
| Web | Vite, React, TypeScript, Tailwind, Plotly |

## Quick start

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8888
```

API docs: http://localhost:8888/docs

The Vite dev server proxies `/api` → `http://127.0.0.1:8888` (override with `OUTLAST_API_URL` in `web/.env`).

### Frontend

```bash
cd web
npm install
npm run dev
```

App: http://localhost:5173

### Tests

```bash
source .venv/bin/activate
pytest
```

## Project layout

```
engine/     # Deterministic simulator (no HTTP)
api/        # FastAPI + SQLite persistence
web/        # React UI
data/       # Tax brackets, config
tests/      # Engine tests + fixtures
```

## Disclaimer

Educational model only — not tax or investment advice. Consult a qualified CPA or CFP.
