# 247jeeves

Retirement tax butler at **247jeeves.com** — rules-based simulator (Phase 1–3).

## Stack

| Layer | Tech |
|-------|------|
| Engine | Python, Pandas/NumPy, YAML rules |
| API | FastAPI, SQLite → PostgreSQL |
| Web | Vite, React, TypeScript, Tailwind, Plotly |

## Quick start

```bash
git clone https://github.com/ukizhake/247jeeves.git
cd 247jeeves
./scripts/dev.sh
```

Or run API and web separately:

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api

#PYTHONPATH=. uvicorn api.main:app --reload --port 8888
```

API docs: http://localhost:8888/docs

The Vite dev server proxies `/api` → `http://127.0.0.1:8888` (override with `JEEVES247_API_URL` in `web/.env`).

### Frontend

```bash
cd web
npm install
npm run dev
```

App: http://localhost:5173

### Debug mode

Add `?debug=1` to the URL to show internal/educational detail that is hidden in the default UI:

- Book and deck terminology (e.g. “Book FA”, chapter references in recommendations)
- Extra simulation columns (phase, spend-rule notes)
- Phase labels on accordions and richer report copy

Examples:

- Local: http://localhost:5173/?debug=1
- Production: https://247jeeves.com/?debug=1

For a production build, you can also set `VITE_DEBUG=true` in Vercel (or `web/.env`) so debug UI is always on — leave it unset for the public site.

Brand logo: `web/public/logo.png` (wordmark; also used as favicon).

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

## Local data

Profiles are stored in `247jeeves.db` (gitignored, project root).

## Repository rename

If your clone still uses an old folder or GitHub name, align them:

1. GitHub → **Settings → General → Repository name** → `247jeeves`
2. `git remote set-url origin https://github.com/ukizhake/247jeeves.git`
3. `mv ~/Projects/<old-folder> ~/Projects/247jeeves` and reopen in your editor

## Disclaimer

Educational model only — not tax or investment advice. Consult a qualified CPA or CFP.
