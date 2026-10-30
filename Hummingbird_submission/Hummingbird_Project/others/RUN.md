# Running Hummingbird locally

Two terminals. Leave both open while you use the app.

These commands are for **Command Prompt (cmd.exe)**, which is what opens by
default on Windows. Note `cd /d` -- plain `cd` will not move between drives, so
`cd F:\...` from `C:\` silently does nothing.

## 1. Backend (the API)

```
cd /d "F:\song recommendation system\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Wait for `indices loaded -- clap=... melody=...` then `Application startup complete`.

## 2. Web app

Open a **second** Command Prompt window:

```
cd /d "F:\song recommendation system\web"
npm run dev
```

<details>
<summary>Using Git Bash or PowerShell instead?</summary>

Forward slashes work there:

```bash
cd "F:/song recommendation system/backend"
../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

```bash
cd "F:/song recommendation system/web"
npm run dev
```
</details>

## 3. Open it

**http://localhost:5173**

---

## Things to try

| Type this | What it shows |
|---|---|
| `bohemian` | A song in the catalog, plus 20 that sound like it |
| `caught in a landslide` | Lyric search — finds Bohemian Rhapsody and quotes the line |
| `gurenge` | A song *not* in the catalog: fetched from iTunes, then analysed |
| **By mood → Jazz** | So What, Take Five |
| **Hum to find** | Hum a catalog song; the browser will ask for microphone access |

Humming covers about 500 songs, so hum something that is in the catalog --
Bohemian Rhapsody or Billie Jean. Humming a song we do not hold returns its
nearest melodic neighbour rather than nothing, which is honest but looks wrong
if you do not know the catalog's limits.

A song found live takes roughly 45 seconds before recommendations appear. That
is CLAP loading its checkpoint the first time; later songs are much quicker
because the model stays in memory.

---

## Other useful URLs

- **http://127.0.0.1:8000/docs** — interactive API documentation. Every
  endpoint with a "Try it out" button. Worth showing in a viva.
- **http://127.0.0.1:8000/health** — confirms the backend is up and reports how
  many tracks are indexed.

---

## If something is wrong

**"Cannot reach the backend"** in the web app — terminal 1 is not running, or
it failed to start. Check that terminal.

**Port already in use** — an old server is still running. On Windows:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

**The microphone does nothing** — browsers only allow recording on `localhost`
or `https`. `localhost:5173` is fine; an IP address like `192.168.x.x` is not.

**No recommendations for a song you just searched** — if it came from iTunes it
has to be analysed first. Wait a few seconds and search again.

---

## Running the mobile app instead

The Expo app in `mobile/` still works and shares the same backend:

```bash
cd mobile && npx expo start
```

Scan the QR code with Expo Go. The phone must be on the same Wi-Fi, and
`API_BASE` in `mobile/src/config.ts` must be the laptop's LAN address --
`scripts/install_gate.py` prints it.
