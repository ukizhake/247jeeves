# Deploy 247jeeves.com

Split hosting:

| Piece | Host |
|-------|------|
| **UI** | Vercel → `https://247jeeves.com` |
| **API** | Mac Mini → Cloudflare Tunnel → `https://api.247jeeves.com` |

Financial data is **not stored on the server** for normal runs (stateless `/api/compute/*`). Vercel serves static files only.

---

## Part 1 — API on Mac Mini

SSH as `sumush2@Macmini`:

```bash
git clone https://github.com/ukizhake/247jeeves.git ~/Projects/247jeeves
cd ~/Projects/247jeeves
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p logs
```

Create `~/Projects/247jeeves/.env`:

```env
CORS_ORIGINS=https://247jeeves.com,https://www.247jeeves.com,https://247jeeves.vercel.app
```

Test manually (optional, one-off):

```bash
cd ~/Projects/247jeeves
export PYTHONPATH="$HOME/Projects/247jeeves"
.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8888
# other tab: curl -s http://127.0.0.1:8888/api/health
```

### Keep API running (launchd — **one job only**)

Use the **user LaunchAgent** only. Do **not** also install a system LaunchDaemon — that duplicates the service and causes confusion.

**One-time install:**

```bash
cd ~/Projects/247jeeves
mkdir -p logs
cp deploy/macmini-api.plist ~/Library/LaunchAgents/com.247jeeves.api.plist

# stop any manual uvicorn first
kill $(pgrep -f "uvicorn api.main:app") 2>/dev/null

launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.247jeeves.api.plist
launchctl enable gui/$(id -u)/com.247jeeves.api
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api
```

**Verify:**

```bash
launchctl print gui/$(id -u)/com.247jeeves.api | grep -E 'state =|pid ='
curl -s http://127.0.0.1:8888/api/health
```

**Restart after code updates** (see Part 5):

```bash
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api
```

Port **8888** (247jeeves). MendonBend stays on **8000**.

**If you accidentally installed a system LaunchDaemon**, remove it and use the Agent above only:

```bash
sudo launchctl bootout system/com.247jeeves.api 2>/dev/null
sudo rm -f /Library/LaunchDaemons/com.247jeeves.api.plist
kill $(pgrep -f "uvicorn api.main:app") 2>/dev/null
# then run the one-time LaunchAgent install again
```

---

## Part 2 — Cloudflare Tunnel for `api.247jeeves.com`

You already run `cloudflared` on the Mini (`com.cloudflare.cloudflared.plist`).

1. **Cloudflare Zero Trust** → Networks → Tunnels → your tunnel → **Public Hostname**
2. Add:
   - Subdomain: `api`
   - Domain: `247jeeves.com`
   - Service: `http://127.0.0.1:8888`
3. Save and restart cloudflared if needed:

   ```bash
   launchctl kickstart -k gui/$(id -u)/com.cloudflare.cloudflared
   ```

4. Test (from any machine):

   ```bash
   curl -s https://api.247jeeves.com/api/health
   ```

See `deploy/cloudflared-api.example.yml` for ingress shape.

**Note:** After moving DNS to Vercel (Part 3), add an **`api`** record in **Vercel DNS** (not Vercel’s web project):

- Type: **CNAME**
- Name: `api`
- Value: `<your-tunnel-id>.cfargotunnel.com` (from Cloudflare tunnel page)

Only the **website** (`@` and `www`) goes to Vercel; **api** points at the tunnel.

---

## Part 3 — Vercel (frontend)

### A. Create project

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import `ukizhake/247jeeves`
2. **Root Directory:** `web` (Edit → set to `web`)
3. Framework: **Vite** (auto-detected)
4. Build: `npm run build` · Output: `dist`

### B. Environment variable

| Name | Value | Environments |
|------|--------|--------------|
| `VITE_API_BASE` | `https://api.247jeeves.com/api` | Production, Preview |

Redeploy after changing env vars (baked in at build time).

### C. Deploy

Push to `main` or click **Deploy** in Vercel. Smoke test:

`https://<project>.vercel.app` → run simulation (needs API up).

---

## Part 4 — Point `247jeeves.com` nameservers to Vercel

1. Vercel → Project → **Settings** → **Domains** → Add `247jeeves.com` and `www.247jeeves.com`
2. Vercel shows **nameservers** (e.g. `ns1.vercel-dns.com`, `ns2.vercel-dns.com`)
3. At your **registrar** (where you bought the domain), replace nameservers with Vercel’s
4. Wait for propagation (minutes to 48h). Vercel will issue HTTPS automatically.

### DNS records (Vercel DNS dashboard)

After NS cutover, Vercel creates web records. **Manually add:**

| Type | Name | Value |
|------|------|--------|
| CNAME | `api` | `<tunnel-id>.cfargotunnel.com` |

Do **not** point `api` at Vercel — only the SPA uses Vercel.

---

## Part 5 — Updates

**Mac Mini API:**

```bash
cd ~/Projects/247jeeves && git pull
.venv/bin/pip install -r requirements.txt -q
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api
```

**Vercel UI:** push to `main` → auto-deploy.

---

## Checklist

- [ ] `curl https://api.247jeeves.com/api/health` → `{"status":"ok",...}`
- [ ] Vercel build has `VITE_API_BASE=https://api.247jeeves.com/api`
- [ ] `https://247jeeves.com` loads UI
- [ ] Simulation works (no CORS / Failed to fetch)
- [ ] `api` CNAME exists in Vercel DNS → Cloudflare tunnel

## Privacy

- Normal runs use stateless `/api/compute/*` — profile sent for that request only, not saved on the Mini
- Legacy `/api/profiles/*` routes still exist in SQLite for future “saved plans”; the public UI does not use them
- No AI / third-party analytics in the app
