# Dent Detection — Frontend

React 18 + Vite UI for the Dent Detection API. It exercises **every** endpoint
and shows each HTTP call as it happens, so the integration is observable rather
than just claimed.

## Running

The backend must be up first:

```bash
# from the project root
python -m waitress --host=127.0.0.1 --port=5055 --threads=6 wsgi:app
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — use `localhost`, not `127.0.0.1`, because Vite
binds to the hostname.

If the backend runs on a different port:

```bash
VITE_PROXY_TARGET=http://127.0.0.1:5000 npm run dev
```

## Why a proxy instead of direct calls

`vite.config.js` proxies `/api` to the backend, so the browser only ever makes
same-origin requests and CORS never comes into it. That removes a whole class of
"works on localhost but not 127.0.0.1" problems. The API log still shows the real
paths.

## Pages

| Page | What it shows | Endpoints |
|---|---|---|
| **Login** | Sign in or register, toggled in place | `POST /auth/register`, `POST /auth/login` |
| **Dashboard** | Score/finding totals, findings by damage type and severity, recent inspections | `GET /stats/summary`, `GET /inspections`, `GET /damage-types` |
| **New Inspection** | Drag-drop upload, live per-file progress, and a step timeline naming the endpoint at each stage | `POST /uploads/signature`, Cloudinary upload, `POST /inspections`, `GET /inspections/{id}/status` |
| **Inspection detail** | Damage score dial, per-class summary, **photos with bounding boxes drawn over them**, photo-quality warnings, raw JSON | `GET /inspections/{id}`, `DELETE /inspections/{id}` |
| **History** | Filter by status / damage type / date range, paginated | `GET /inspections` |
| **System & API** | Readiness of database, model and Cloudinary; the six damage classes; a table of all 15 routes with a **Run** button on the safe ones | `GET /health/ready`, `GET /damage-types`, and whichever route you run |

## The API Activity panel

Docked at the bottom of every page. Every request made through `src/api/client.js`
is recorded there with its method, status, duration and the backend's
`X-Correlation-Id`. Nothing can bypass it — the client is the only place `fetch`
is called, and it reports to the panel on every request including failures.

## How the upload works

The browser never sees the Cloudinary API secret. It asks the backend to sign an
upload, receives the signed parameters, and posts the file directly to
Cloudinary. Only the returned `public_id` and `secure_url` are then sent to our
API. `XMLHttpRequest` is used rather than `fetch` for the upload, purely because
`fetch` cannot report upload progress.

The parameters posted to Cloudinary must match exactly what the backend signed
(`folder` and `timestamp`), or Cloudinary rejects the signature.

## Bounding box overlay

Detections are stored in the coordinate space of the **original** photo, so the
overlay is an SVG whose `viewBox` is the image's own dimensions, layered over the
`<img>`. It therefore scales correctly at any display size with no manual
arithmetic. Hovering a box highlights its row and vice versa.

## Client-side validation

Files are checked for type, size (10 MB) and minimum dimension (320px) before
upload, so the user gets immediate feedback instead of a 422 after a slow upload.
The backend validates the same rules regardless — this is a convenience, not the
enforcement point.

## Layout

```
src/
  api/client.js           the only place fetch is called; attaches JWT, logs everything
  context/AuthContext     session, token persistence, restore-on-refresh
  context/ApiLogContext   ring buffer behind the API Activity panel
  components/
    AnnotatedShot.jsx     photo + SVG bounding boxes
    ApiLogPanel.jsx       the live request log
    common.jsx            badges, gauge, alerts, empty states
  pages/                  one file per screen
  styles.css              hand-written; no CSS framework
```
