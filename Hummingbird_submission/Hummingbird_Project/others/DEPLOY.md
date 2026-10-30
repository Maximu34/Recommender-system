# Deploying the Hummingbird backend

The deployed service is **JSON only** — roughly 2.4 MB of index artifacts, no
audio. Clients stream 30s clips straight from Apple's CDN, so there is nothing
to host and no object storage to pay for.

**Fly.io**, not Render, for two concrete reasons: Fly builds on a remote
builder (so no local Docker is needed) and deploys from a local directory (so
no GitHub remote is needed). Neither Docker nor a git remote exists on the dev
machine.

---

## What only you can do

Three things need your own account and cannot be automated:

1. **A Fly.io account** — sign up at https://fly.io and add a card. Small apps
   run inside the monthly allowance, but a card is required to create one.
2. **`fly auth login`** — opens a browser against your account.
3. **Setting the database secret** — it contains your Supabase password.

---

## Steps

### 1. Install flyctl

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Then reopen the terminal so `flyctl` is on PATH.

### 2. Sign in and create the app

```bash
fly auth login
fly apps create hummingbird-api
```

If that name is taken, pick another and change `app` in `fly.toml` to match.

### 3. Give it the database

Copy the `POSTGRES_URL` line out of `backend/.env` and set it as a secret, so
it is stored encrypted rather than baked into the image:

```bash
fly secrets set POSTGRES_URL='<the POSTGRES_URL line from backend/.env>'
```

Use single quotes — the password contains characters the shell would otherwise
interpret.

### 4. Deploy

```bash
fly deploy
```

First build takes a while: it installs torch and bakes in the 586 MB CLAP
checkpoint. Later deploys reuse those layers.

### 5. Point the app at it

```bash
fly status          # shows the hostname
```

Put that URL in `mobile/src/config.ts` as `API_BASE`, with `https://`.

---

## Checks after deploying

```bash
curl https://<your-app>.fly.dev/health
```

Expect `"db":"postgres"` and `"tracks":511`. Then:

```bash
curl "https://<your-app>.fly.dev/find?q=caught%20in%20a%20landslide"
```

Expect Bohemian Rhapsody, with the matching lyric line.

---

## If it cannot reach the database

The most likely failure, and it is worth knowing in advance. `backend/.env`
uses Supabase's **direct** connection, whose hostname resolves to **IPv6 only**
— verified from the dev machine, which has IPv6. If Fly's egress cannot reach
it, the app will start and then fail every database call.

The fix is to switch to the **Session pooler** connection string, which is
IPv4-reachable. Get it from the Supabase dashboard (Connect → Session pooler,
port 5432) and re-run `fly secrets set POSTGRES_URL='...'`. The code needs no
change: it already parses either form, and disables prepared statements
automatically if you use the transaction pooler on 6543.

## Cost

The 1 GB machine in `fly.toml` exists so mood search works — CLAP is about
1 GB resident. Everything else (`/search`, `/similar`, `/hum`) fits in roughly
210 MB, because CLAP is imported lazily inside `similar_by_text`.

Dropping to 512 MB is safe **only** if you accept that mood search will be
OOM-killed. It is the most impressive feature in the app, so this is a bad
place to economise.
