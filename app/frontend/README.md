# Nilytics Frontend

Vite + React + TypeScript, with TanStack Table, TanStack Query, and Tailwind CSS. Uses pnpm.

## Setup

```bash
cd app/frontend
pnpm install
```

## Dev

With the Go API running on port 8080:

```bash
pnpm dev
```

Open http://localhost:5173. API requests to `/api/*` are proxied to http://localhost:8080 (e.g. `fetch('/api/players')` → `GET http://localhost:8080/players`).

## Build

```bash
pnpm build
```

Output is in `dist/`. Preview with `pnpm preview`.

## Docker

From repo root: `make frontend-build` then `make frontend-run` (or `docker compose up -d frontend`). The app is served on http://localhost:5173; `/api` is proxied to the `api` service. Ensure the API is running (`docker compose up -d api`).

### Nginx config

The Docker image uses nginx to serve the built app. The config in `nginx.conf` does three things:

1. **Serving static files** – Tells nginx where the built assets live (`/usr/share/nginx/html`, i.e. `dist/`) and to use `index.html` as the default document.

2. **SPA fallback** – `try_files $uri $uri/ /index.html` sends unknown paths (e.g. `/players` or on refresh) to `index.html` so the React router can handle them instead of nginx returning 404.

3. **API proxy** – `location /api/` forwards requests to the `api` container. In the container the browser only talks to the frontend; without this proxy, `fetch('/api/players')` would hit nginx and 404. With it, those requests are proxied to the backend like in dev with Vite.
