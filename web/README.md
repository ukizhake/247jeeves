# 247jeeves web

Vite + React UI for [247jeeves.com](https://247jeeves.com).

```bash
npm install
npm run dev
```

Dev server: http://localhost:5173 (proxies `/api` to the FastAPI backend on port 8888).

Production build: `npm run build` → `dist/` (served by nginx or similar; see root `README.md`).
