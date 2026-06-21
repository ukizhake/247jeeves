# 247jeeves — setup commands

| Environment | URL |
|-------------|-----|
| Local dev | http://localhost:5173 |
| Production UI | https://247jeeves.com (Vercel) |
| Production API | https://api.247jeeves.com (Mac Mini + Cloudflare tunnel) |

---

## 1. Local dev (your laptop)

```bash
cd ~/Projects/247jeeves
git clone https://github.com/ukizhake/247jeeves.git   # first time only

# If .venv broken after folder rename:
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cd web && npm ci && cd ..

./scripts/dev.sh
```

- UI: http://localhost:5173  
- API: http://localhost:8888/api/health  
- Debug UI (phase labels): http://localhost:5173/?debug=1  

```bash
# If port 8888 busy:
lsof -nP -iTCP:8888 -sTCP:LISTEN
kill <PID>

# Tests
source .venv/bin/activate
PYTHONPATH=. pytest
```

---

## 2. Mac Mini — API (`sumush2@Macmini`)

```bash
ssh sumush2@Macmini
cd ~/Projects/247jeeves
git pull origin main

# First time only:
git clone https://github.com/ukizhake/247jeeves.git ~/Projects/247jeeves
cd ~/Projects/247jeeves
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p logs
```

`~/Projects/247jeeves/.env`:

```env
CORS_ORIGINS=https://247jeeves.com,https://www.247jeeves.com,https://247jeeves.vercel.app
```

### Run API via launchd (survives SSH close + reboot)

**One job only:** user LaunchAgent at `gui/$(id -u)/com.247jeeves.api`. Do not also install a system LaunchDaemon.

```bash
cd ~/Projects/247jeeves
mkdir -p logs
cp deploy/macmini-api.plist ~/Library/LaunchAgents/com.247jeeves.api.plist
kill $(pgrep -f "uvicorn api.main:app") 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.247jeeves.api.plist
launchctl enable gui/$(id -u)/com.247jeeves.api
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api
```

```bash
curl -s http://127.0.0.1:8888/api/health
launchctl print gui/$(id -u)/com.247jeeves.api | grep -E 'state =|pid ='
tail -20 ~/Projects/247jeeves/logs/api.log
```

Port **8888** = 247jeeves. MendonBend stays on **8000**.

### Mac Mini git (match GitHub, no local commits)

```bash
cd ~/Projects/247jeeves
git fetch origin
git reset --hard origin/main
```

---

## 3. Mac Mini — Cloudflare tunnel (`api.247jeeves.com`)

Tunnel: `wattstackup-ollama` · ID: `979c3781-6b3b-4a07-ac08-d7f0251b2c83`

`~/.cloudflared/config.yml`:

```yaml
tunnel: 979c3781-6b3b-4a07-ac08-d7f0251b2c83
credentials-file: /Users/sumush2/.cloudflared/979c3781-6b3b-4a07-ac08-d7f0251b2c83.json

ingress:
  - hostname: api.247jeeves.com
    service: http://127.0.0.1:8888
  - hostname: mendonbend.com
    service: http://127.0.0.1:8000
  - hostname: www.mendonbend.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

```bash
launchctl kickstart -k gui/$(id -u)/com.cloudflare.cloudflared
cloudflared tunnel list
curl -s https://api.247jeeves.com/api/health
```

DNS CNAME (Vercel DNS or Namecheap Advanced DNS):

| Type | Name | Value |
|------|------|--------|
| CNAME | `api` | `979c3781-6b3b-4a07-ac08-d7f0251b2c83.cfargotunnel.com` |

---

## 4. Vercel — frontend

1. Import existing repo: `ukizhake/247jeeves` (do **not** create a new GitHub repo)
2. Project name: e.g. `247jeeves-web` (any free name)
3. **Framework preset:** Vite
4. **Root directory:** `web`
5. Build: `npm run build` · Output: `dist`

Environment variable (Production + Preview):

```text
VITE_API_BASE=https://api.247jeeves.com/api
```

Redeploy after changing env vars.

---

## 5. DNS — Namecheap → Vercel

1. Vercel → Project → **Settings → Domains** → add `247jeeves.com` and `www.247jeeves.com`
2. Copy Vercel nameservers (typically `ns1.vercel-dns.com`, `ns2.vercel-dns.com`)
3. Namecheap → Domain List → **247jeeves.com** → Manage → **Nameservers** → Custom DNS → paste Vercel NS
4. Vercel DNS → add `api` CNAME (see section 3)

`@` and `www` are usually automatic once NS point at Vercel.

---

## 6. Deploy updates

**Laptop → GitHub:**

```bash
cd ~/Projects/247jeeves
git add -A
git commit -m "Your message."
git push origin main
```

**Mac Mini API:**

```bash
ssh sumush2@Macmini
cd ~/Projects/247jeeves
git pull origin main
.venv/bin/pip install -r requirements.txt -q
launchctl kickstart -k gui/$(id -u)/com.247jeeves.api
```

**Vercel UI:** auto-deploys on push to `main`.

---

## 7. Smoke tests

```bash
curl -s https://api.247jeeves.com/api/health
curl -sI https://247jeeves.com | head -3
```

Browser: https://247jeeves.com → Run simulation (no “Failed to fetch”).

---

## 8. Husband — private local copy (optional)

```bash
git clone https://github.com/ukizhake/247jeeves.git
cd 247jeeves
./scripts/dev.sh
```

Data stays on his machine only (`247jeeves.db`). No AI; profiles not sent to models.
