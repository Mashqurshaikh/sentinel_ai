# Sentinel frontend

React + Vite + Tailwind v4 + Framer Motion + Recharts. Talks to the FastAPI
backend in `../backend` over REST and a WebSocket for the live feed.

## Run locally

```bash
npm install
npm run dev
```

Opens on http://localhost:5173. The dev server proxies `/api/*` to
`http://localhost:8000` (see `vite.config.js`) - start the backend first
(`uvicorn backend.main:app --reload` from the project root).

## Pages

- **Overview** (`/`) - landing page, live stat summary
- **Gateway** (`/gateway`) - the scanner: paste a prompt or upload a file
- **Dashboard** (`/dashboard`) - live feed, activity charts, agent triggers
- **Approvals** (`/approvals`) - review queue for blocked requests: approve or reject with a name attached
- **Policy Rules** (`/policy`) - add/remove custom detection regex rules
- **Reports** (`/reports`) - compliance tag breakdown, CSV export
- **Integrations** (`/integrations`) - what this plugs into next

## Build for production

```bash
npm run build
```

Outputs to `dist/`. Serve it with any static file server, or point
`VITE_API_BASE` / `VITE_WS_BASE` env vars at a non-localhost backend before
building if the API isn't on the same host.
