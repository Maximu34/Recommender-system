# Hummingbird — web client

React + Vite + TypeScript. Talks to the same FastAPI backend as everything
else; the API needed no changes for the web build.

```bash
npm install
npm run dev          # http://localhost:5173
```

The backend must be running:

```bash
cd ../backend && ../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

Point it elsewhere with `VITE_API_BASE`, e.g. a deployed instance:

```bash
VITE_API_BASE=https://your-app.fly.dev npm run build
```

## Two things verified rather than assumed

**Clips stream from Apple's CDN, not from our backend.** Apple serves them with
`Access-Control-Allow-Origin: *` and honours range requests, so playback and
seeking work cross-origin. A media element would not need CORS at all, but
having it means Web Audio analysis would also work.

**Humming needs no conversion.** `MediaRecorder` produces webm/opus in Chrome
and Firefox and mp4 in Safari; the backend decodes with PyAV, which handles all
three. `getUserMedia` requires a secure context — localhost in development,
HTTPS once deployed.
