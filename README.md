# Dent Detection Backend

Flask + PostgreSQL backend for the AutoDent vehicle damage inspection system.
A client uploads car photos to Cloudinary, this service runs the YOLO11m model
over them, and returns a structured damage report which is kept as history.

See [`docs/SCOPE_OF_WORK.md`](docs/SCOPE_OF_WORK.md) for what the project does
and [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md) for the model and pipeline
specification this implements.

---

## The model

| | |
|---|---|
| Architecture | **YOLO11m** (Ultralytics), fine-tuned from `yolo11m.pt` |
| Task | Object detection — bounding boxes, no segmentation masks |
| Dataset | CarDD (`/content/cardd/data.yaml`) |
| Weights | `models/best.pt` (40 MB) |
| Classes | `dent`, `scratch`, `crack`, `glass shatter`, `lamp broken`, `tire flat` |

All of the above was read out of `best.pt` itself, not taken on trust from the
docs. Two things differ from `docs/DOCUMENTATION.md`, which describes the model
as YOLOv8:

- It is **YOLO11**, so `ultralytics>=8.3` is required. Older versions cannot
  load these weights.
- There is **no mirror class**. An earlier draft of the scope listed mirror
  damage; this model cannot detect it.

Confirm what the model can see at any time:

```bash
flask --app wsgi check-model
```

---

## Setup

Requires Python 3.12 and a running PostgreSQL 14+.

```bash
# 1. Virtual environment
py -3.12 -m venv .venv
.venv\Scripts\activate

# 2. Dependencies. Install CPU-only torch first, or pip pulls ~2.5GB of CUDA wheels.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Configuration
copy .env.example .env
#    then set DB_PASSWORD, and the CLOUDINARY_* values

# 4. Database - creates it, builds the schema from the models, seeds the lookups
python scripts/create_database.py
flask --app wsgi init-db

# 5. Run
flask --app wsgi run
```

The API is then on `http://localhost:5000`, with `/api/v1/health` as the
liveness check and `/api/v1/health/ready` reporting database and model status.

### With the UI

There is a React frontend in [`frontend/`](frontend/README.md) that exercises
every endpoint and shows each call live. Run the backend on 5055 and the UI
against it:

```bash
python -m waitress --host=127.0.0.1 --port=5055 --threads=6 wsgi:app   # terminal 1
cd frontend && npm install && npm run dev                              # terminal 2
```

Then open **http://localhost:5173** (use `localhost`, not `127.0.0.1` — Vite
binds to the hostname).

### Running without Cloudinary or the weights

Set `MODEL_BACKEND=mock` to run against a synthetic model that emits the same
six labels. Useful for frontend work and required by the test suite. Cloudinary
is only needed by `POST /uploads/signature`; everything else works without it.

---

## Configuration

Every setting is an environment variable — see `.env.example` for the full list.
The ones that change behaviour most:

| Variable | Default | Notes |
|---|---|---|
| `MODEL_BACKEND` | `ultralytics` | `mock` for a synthetic model, no weights needed |
| `MODEL_PATH` | `models/best.pt` | The weights file |
| `MODEL_CONFIDENCE_THRESHOLD` | `0.35` | Balanced. `0.22` sensitive, `0.50` strict |
| `MODEL_IOU_THRESHOLD` | `0.45` | Overlap threshold for class-aware NMS |
| `MODEL_INPUT_SIZE` | `640` | Lower is faster but misses fine scratches |
| `MODEL_FALLBACK_ENABLED` | `false` | Retry lower with TTA when a pass finds nothing - ~2x cost when it fires |
| `MODEL_USE_CLAHE` | `false` | Contrast boost for glare and shadow |
| `INFERENCE_WORKERS` | `2` | Each worker holds its own copy of the model |

Detection thresholds and the damage-score weights live in `config/` rather than
in code, so they can be tuned without a release:

- `config/class_mapping.json` — model label → internal class key
- `config/severity_rules.json` — per-detection severity bands and the 0–100 score

---

## How a request flows

1. `POST /api/v1/uploads/signature` — the backend signs a Cloudinary upload so
   the browser can upload directly. The API secret never leaves the server.
2. The frontend uploads one photo per side to Cloudinary and gets back a
   `secure_url` for each.
3. `POST /api/v1/inspections` with those URLs keyed by side. The backend stores the
   inspection, returns **202** with an id, and queues the work — the client is
   never held open for the length of inference.
4. In the background, per image: download → EXIF-correct → model → clamp boxes →
   class-aware NMS → map labels → severity → store.
5. Per-image findings are aggregated into one report with a 0–100 damage score.
6. `GET /api/v1/inspections/{id}` returns the finished report.

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/health` | – | Liveness |
| `GET` | `/api/v1/health/ready` | – | Database + model readiness |
| `POST` | `/api/v1/auth/register` | – | Create account |
| `POST` | `/api/v1/auth/login` | – | Get tokens |
| `POST` | `/api/v1/auth/refresh` | refresh | Rotate access token |
| `GET` | `/api/v1/auth/me` | ✓ | Current user |
| `POST` | `/api/v1/auth/logout` | ✓ | Revoke the access token used on this request |
| `DELETE` | `/api/v1/auth/me` | ✓ | Soft-delete the caller's own account |
| `POST` | `/api/v1/uploads/signature` | ✓ | Signed Cloudinary upload params |
| `POST` | `/api/v1/inspections` | ✓ | Submit photos by side → 202 ([shape](#submitting-an-inspection)) |
| `GET` | `/api/v1/inspections` | ✓ | History, paginated and filterable by customer, vehicle type, status, damage type, date |
| `GET` | `/api/v1/inspections/{id}` | ✓ | Full inspection + report |
| `GET` | `/api/v1/inspections/{id}/status` | ✓ | Lightweight poll |
| `GET` | `/api/v1/inspections/{id}/report` | ✓ | Report only |
| `DELETE` | `/api/v1/inspections/{id}` | ✓ | Soft delete |
| `GET` | `/api/v1/damage-types` | – | The six classes, with UI colours |
| `GET` | `/api/v1/vehicle-types` | – | Car body styles for the submission form |
| `GET` | `/api/v1/detection-presets` | – | Sensitivity modes |
| `GET` | `/api/v1/stats/summary` | ✓ | Counts by class and severity |

Errors are uniform:

```json
{ "error": { "code": "IMAGE_UNREACHABLE", "message": "...", "details": {} } }
```

---

## Data model

Five tables. The customer name and vehicle type are columns on `inspections`
rather than a table of their own — they only ever describe the inspection they
were submitted with, so a join bought nothing.

| Table | Holds |
|---|---|
| `users` | Accounts. Soft-deletable. |
| `inspections` | One submission. This row *is* the history record — see below. |
| `inspection_images` | One row per photo — its view angle, Cloudinary references and quality diagnostics. Binaries never live in the database. |
| `detections` | One damage instance found in one image: class, confidence, severity, box. |
| `damage_types` | Seeded lookup for the six classes, with UI colours. Not user-editable. |

Deletes cascade from `users` → `inspections` → `inspection_images` → `detections`.

### Why each `inspections` column exists

Every column is read by the API or needed to run the job; nothing is written and
then ignored.

**Ownership**

| Column | Why |
|---|---|
| `id` | UUID primary key, and the only handle a client gets. Non-sequential, so one id does not reveal how many others exist. |
| `user_id` | Who submitted it. Scopes every read and cascades on account deletion. |
| `customer_name` | Who the inspection is *for* — not the account holder, since one surveyor account submits work for many customers. Indexed: the history page searches it. |
| `vehicle_type` | Car **body style** (`sedan`, `suv`, `hatchback`…). Everything here is a car, so this is the shape, not the category. Indexed: reporting slices by it, and the same dent reads differently on a hatchback tailgate than an SUV rear quarter. |

**Identity and lifecycle**

| Column | Why |
|---|---|
| `status` | `queued → processing → completed / partial_success / failed`. Indexed: the most-used history filter, and what the client polls. |
| `idempotency_key` | Set from the `Idempotency-Key` header. Unique, so a retry or double-clicked submit returns the original instead of creating a twin. |
| `created_at` / `updated_at` | Ordering and audit. `created_at` is indexed with `user_id` because the list is always "this user's, newest first". |
| `deleted_at` | Soft delete. History is never destroyed — a deletion hides the row and its findings stay. |

**Headline result** — denormalised on purpose, so the history list and dashboard
render from one query instead of aggregating detections per row.

| Column | Why |
|---|---|
| `overall_severity` | Worst severity across the inspection: the one-word answer. |
| `damage_score` | Aggregate 0–100 score. Stored so history rows can sort and filter on it. |
| `total_detections` | How many findings were kept. Lets the poll endpoint report progress without counting rows. |
| `total_area_percent` | Mean share of each analysed photo showing damage. Averaged, not summed — five photos at 60% each is 60%, not 300%. |
| `damage_summary` | Per-class counts as JSON. This is what makes a 20-row history page one query rather than 20 aggregates. |
| `below_threshold_count` | In-scope findings the confidence threshold excluded. Surfaced so a thin report reads as "3 more below 0.35" instead of looking like the model missed the damage. |

**Reproducibility** — raw model output is not retained, so these are what let a
surprising report be explained.

| Column | Why |
|---|---|
| `detection_preset` | The preset the caller chose, e.g. `balanced` or `sensitive+custom`. |
| `detection_settings` | The exact conf/iou/imgsz/augment used for this run. |
| `model_name`, `model_version`, `model_backend` | Which model produced the findings. Per-inspection because weights can be swapped between runs, and an old report must not appear to have come from the current model. |

**Timing and failure**

| Column | Why |
|---|---|
| `processing_completed_at` | When the job finished; doubles as the report's `generated_at`. |
| `processing_ms` | Wall-clock duration. Shown in the UI and used to spot a model or host that has become slow. |
| `error_code` / `error_message` | A code the client can branch on plus a message it can show. Both null on success. |

Three things are deliberately **not** columns:

- `image_count` is a property returning `len(images)`. The images are eager-loaded
  anyway, so a stored copy could only drift away from the rows it counts.
- `processing_started_at` was removed — it was written by the job and never read.
- `reference_code` was removed. It existed to give humans something quotable, but
  `customer_name` already fills that role in the UI, and `id` is the machine
  handle — so it was a third identifier earning its keep in neither role.

`flask init-db` creates missing tables but cannot alter existing ones, so an
older database is brought in line with the models by:

```bash
python scripts/sync_schema.py           # show what would change
python scripts/sync_schema.py --apply   # do it (pg_dump first)
```

It inspects the live schema first, so it only does what is still outstanding and
is safe to re-run.

---

## Background processing

Inference takes seconds per image, so it runs outside the request. There is no
Redis or Docker on the current target machine, so instead of Celery the work
runs in a **thread pool inside the Flask process** (`app/tasks/queue.py`).

The trade-off: queued jobs live in memory and are lost if the process restarts.
`requeue_stuck_inspections()` recovers anything left in `processing` on the next
boot. `enqueue()` is deliberately Celery-shaped, so moving to a real broker
later means reimplementing that one function and touching no callers.

---

## Damage score

From `DOCUMENTATION.md` section 4:

```
score = min(100, (critical × 25) + (count × 8) + min(40, total_area% × 4))
```

`glass_shatter`, `lamp_broken` and `tire_flat` are treated as critical — the
documentation gives the formula but not the list, so this is an assumption worth
confirming. It lives in `config/severity_rules.json`. Bands: 0 none, 1–24 minor,
25–59 moderate, 60+ severe.

Be aware the score **saturates**: past roughly a dozen findings everything reads
100, so it separates light from heavy damage but not heavy from catastrophic.

`total_area_percent` is the **mean** damaged area across the analysed images,
not the sum. Summing is tempting but meaningless — five images at 60% each would
report "300% damaged". The mean answers "how much of the vehicle we photographed
shows damage" and stays comparable between a 2-image and a 5-image inspection.

### Sensitivity is the single biggest lever on what gets reported

The confidence threshold decides what appears in a report, and per
`DOCUMENTATION.md` section 6 the most common cause of "the model missed obvious
damage" is that threshold, not the model. Faint dents and cracks routinely score
**0.15–0.30**, so the documented default of 0.35 excludes them.

Sensitivity is therefore chosen **per inspection**, not per deployment:

```json
POST /api/v1/inspections
{ "images": [...], "settings": { "preset": "sensitive" } }
```

| Preset | conf | Use for |
|---|---|---|
| `balanced` | 0.35 | Good-quality photos. The default. |
| `sensitive` | 0.22 | Faint scratches, shallow dents. More false positives. |
| `strict` | 0.50 | Formal claims, where a false positive is costly. |

`GET /api/v1/detection-presets` serves these, so clients don't keep their own
copy of the numbers. Explicit `confidence` / `iou` / `input_size` / `augment`
values may be sent instead of, or on top of, a preset.

Whatever was used is stored on the inspection and returned in the report, so any
result can be explained and reproduced.

**Nothing is dropped silently.** The model always runs at `MODEL_DETECTION_FLOOR`
(0.15) and the backend filters afterwards — Ultralytics applies `conf` after the
forward pass, so the lower floor costs nothing. Findings between the floor and
the chosen threshold are counted and reported as `below_threshold_count`, so a
thin report says *"3 more findings below 0.35"* rather than looking like the model
saw nothing. `flask reprocess <id>` can then re-run at a lower threshold.

### The model reports on what it is given

The model has no notion of "this is not a car". Run it on an arbitrary photo and
it will still emit boxes — in testing, a stock photo of two people produced two
`glass shatter` detections at ~0.55 confidence. There is no vehicle-presence
gate in this backend, so if users can submit arbitrary images, expect confident
findings on non-vehicle photos. Worth deciding whether to add one.

---

## Detection recall

Enhancements 1–4 from `DOCUMENTATION.md` section 7 are implemented, because the
usual cause of a missed detection is the photo rather than the model:

| | Enhancement | Where |
|---|---|---|
| 1 | EXIF orientation correction | `app/inference/preprocess.py` |
| 2 | Low-confidence fallback pass with TTA | `app/inference/ultralytics_adapter.py` |
| 3 | CLAHE contrast boost (opt-in) | `app/inference/preprocess.py` |
| 4 | Blur / exposure diagnostics | `app/inference/preprocess.py` |
| 5 | Sliding-window tiling (SAHI) | **not implemented** — see below |

Enhancement 5 is deliberately left out: it multiplies inference cost by the tile
count, which on CPU-only hardware would push a 5-image inspection well past a
minute. Worth adding once there is a GPU, or as an opt-in "deep scan" mode.

Photo-quality warnings are returned in the report as
`report.image_quality_warnings`, so a user whose report comes back empty is told
their photo was blurry or dark instead of being left to guess.

---

## Tests

```bash
pytest                      # 106 unit + integration tests
pytest --cov=app            # with coverage
```

These run on in-memory SQLite with the mock model and stubbed image downloads,
so they need no PostgreSQL, no Cloudinary, no weights and no network. The models
avoid Postgres-only column types so the same schema works on both engines.

For a check against the **real** stack — live API, PostgreSQL and the actual
YOLO weights — start the server and run the smoke test. It covers 47 assertions
across auth, the Cloudinary signature, the full inspection pipeline, history,
ownership isolation and soft delete, using read-only public images from
Cloudinary's demo account so nothing is uploaded to your own:

```bash
python -m waitress --port=5055 wsgi:app     # in one terminal
python scripts/smoke_test.py                # in another
```

Try the real model on a local file without touching the API or database:

```bash
python scripts/verify_model.py path\to\car.jpg
python scripts/verify_model.py path\to\car.jpg --conf 0.22 --clahe
```

---

## Layout

```
app/
  __init__.py         application factory
  config.py           environment-driven settings
  errors.py           error types + uniform JSON envelope
  logging_config.py   structured JSON logs with a correlation id
  seed.py             the six damage_types rows
  api/v1/             routes only: validate, call a service, serialise
  services/           business logic
  models/             SQLAlchemy models
  schemas/            Pydantic request validation
  inference/          the model seam - see below
  tasks/              background worker and the inspection job
  utils/              pagination, UUID parsing, Cloudinary URLs,
                      cached JSON config, image formats
config/               tunable JSON: class mapping, severity rules
scripts/              create_database.py, sync_schema.py, verify_model.py
tests/
```

The models are the single source of truth for the schema — there is no migration
history to keep in step with them. `flask --app wsgi init-db` creates anything
missing and seeds the lookup table.

`app/inference/` is the seam that keeps the model swappable. `base.py` defines
the `DamageDetector` contract, `registry.py` picks an adapter from
`MODEL_BACKEND`, and `normalizer.py` converts whatever the model emits into one
canonical shape. Nothing above that layer knows which model is loaded — proven
by the test suite, which runs the entire stack against `mock`.

Swapping in a retrained model is: drop in the `.pt`, point `MODEL_PATH` at it,
and add any new labels to `config/class_mapping.json`. No code change.

---

## Audit trail

Each inspection records the model that produced its findings (`model_name`,
`model_version`, `model_backend`) and the exact settings it ran with
(`detection_preset`, `detection_settings`), so any report can be explained.

Reports are built from the stored detections, never from the live model, so a
change to the report wording or the severity thresholds is picked up by old
inspections immediately. Raw per-image model output is **not** retained, so
changing the detection thresholds themselves means re-running inference:

```bash
flask --app wsgi reprocess <inspection-id>
```

Inspections are soft-deleted, so history is never destroyed.

---

## Notes for production

- Inference on CPU takes several seconds per image. A GPU (`pip install torch
  --index-url .../cu121`) brings that to tens of milliseconds and is the single
  biggest win available.
- Run under a real WSGI server: `waitress-serve --port=5000 wsgi:app` on
  Windows, gunicorn on Linux.
- `SECRET_KEY` and `JWT_SECRET_KEY` must be long random values, and at least 32
  bytes or PyJWT will warn on every token.
- Keep `INFERENCE_WORKERS` low — each worker loads its own copy of the model.
- If more than one web process is run, move the queue to Celery/Redis first;
  the in-process pool does not share work between processes.

---

## Submitting an inspection

`POST /api/v1/inspections` takes the customer, the vehicle type, and one photo
URL per side of the vehicle. The photos are uploaded to Cloudinary first (see
[How a request flows](#how-a-request-flows)); only their URLs are sent here.

```json
{
  "customer_name": "test",
  "vehicle_type": "car",
  "images": {
    "front": "https://res.cloudinary.com/<cloud>/image/upload/v1787118301/dent-inspections/c1ee4j9ff0avmp8xzorz.jpg",
    "back":  "https://res.cloudinary.com/<cloud>/image/upload/v1787118303/dent-inspections/bun1fddsgg9vac2kt4nd.jpg",
    "left":  "https://res.cloudinary.com/<cloud>/image/upload/v1787118304/dent-inspections/fzutxlljmpqultgobbuu.jpg",
    "right": "https://res.cloudinary.com/<cloud>/image/upload/v1787118306/dent-inspections/lopcrypbi5wgr1vkkev0.jpg",
    "top":   "https://res.cloudinary.com/<cloud>/image/upload/v1787118308/dent-inspections/eqi4c3wwkomm9ephao1j.jpg"
  },
  "settings": { "preset": "balanced" }
}
```

| Field | Required | Notes |
|---|---|---|
| `customer_name` | ✓ | Whitespace collapsed. Max 150 chars. |
| `vehicle_type` | ✓ | Lower-cased so it groups in history and stats. Max 40 chars. |
| `images` | ✓ | Keyed by side. Allowed keys: `front`, `back`, `left`, `right`, `top`. |
| `settings` | – | Sensitivity preset or explicit `conf`/`iou`/`imgsz`. |

Notes on `images`:

- Keys are the view angle, so a photo can never disagree with the side it is
  labelled as. Any unrecognised key is a 422.
- Send all five, or any subset — a side you leave out is simply absent from the
  report. At least one is required.
- Each URL must be `https` and distinct; the same photo submitted as two sides
  is a 422.
- Order does not matter. Photos are stored and reported `front, back, left,
  right, top` regardless of JSON key order.
- The Cloudinary public id is derived from the URL, so nothing else about the
  upload needs sending. Images smaller than 320px on the short side are rejected
  per-image after download, and the rest of the inspection still completes.

Send `Idempotency-Key` to make a retry or a double-clicked submit safe.

The response is **202** with the inspection id; poll
`GET /api/v1/inspections/{id}/status` until `is_finished`, then read the report.

History can be filtered by `?customer_name=` (partial, case-insensitive) and
`?vehicle_type=` (exact), alongside `?status=`, `?damage_type=`, `?date_from=`
and `?date_to=`.











cd /var/www/html/prorev-ai-model
sudo systemctl restart prorev-ai-model



test@yopmail.



sudo systemctl stop prorev-ai-model
sudo -u postgres psql -d dent_detection