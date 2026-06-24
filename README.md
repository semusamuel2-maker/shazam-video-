# Canadian Real Estate Investment Data Platform — v1

A "PropStream for Canada" investment-research platform. This repository contains the
**v1 scaffold**, deliberately scoped to what is *legitimately buildable today without
commercial data licenses*:

- **Layer C — distress / motivation signals** (public tax-sale notices + signals derived
  from licensed layers). This is the v1 sweet spot and the data we actually ingest here.
- **Compliance core** — the real moat: per-source license-rule enforcement, PIPEDA data
  handling, a CASL consent state machine, and per-record data provenance / audit trail.
- **Licensed layers (A title, B assessment, D MLS, E skip-trace) stubbed behind
  provider interfaces** — no live data, but the seams are in place so a signed data
  agreement is a config + adapter change, not a re-architecture.

> ⚠️ **Read this first.** The original build spec is explicit (its §2 and §10): *legal and
> data-licensing validation come before engineering.* Layers A/B/D/E depend on commercial
> agreements with Teranet, LTSA, MPAC, BC Assessment, and CREA/boards. **Nothing in this
> repo scrapes those sources, and you must not wire one in until counsel and a license are
> in place.** See [`docs/LEGAL.md`](docs/LEGAL.md).

## What's in the box

| Area | Status | Where |
|------|--------|-------|
| Data model (all §8 entities) | ✅ built | `app/models/` |
| Layer C ingestion (public tax sales) | ✅ built | `app/ingestion/sources/` |
| Derived signals (absentee, long-held) | ✅ built | `app/ingestion/derived_signals.py` |
| License-rule enforcement | ✅ built | `app/compliance/license_rules.py` |
| CASL consent state machine | ✅ built | `app/compliance/casl.py` |
| PIPEDA helpers + provenance/audit | ✅ built | `app/compliance/` |
| Search / property / list / outreach API | ✅ built | `app/api/` |
| Comp estimate (title+assessment, no MLS) | ✅ built | `app/services/comps.py` |
| Layer A/B/D/E providers | 🔌 stubbed | `app/providers/` |
| Map-centric frontend | 🪧 minimal demo | `frontend/` |

## Quick start

```bash
# 1. Install (Python 3.11+)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Run the test suite (uses SQLite — no Postgres needed)
pytest

# 3. Seed sample public data + run the API
python -m scripts.seed
uvicorn app.main:app --reload
# -> http://localhost:8000/docs  (OpenAPI)
# -> http://localhost:8000/      (minimal map demo)
```

### Production database (PostGIS)

The scaffold runs on SQLite for tests and quick demos. For real spatial queries use
PostGIS:

```bash
docker compose up -d db          # Postgres 16 + PostGIS
export DATABASE_URL="postgresql+psycopg://prop:prop@localhost:5432/prop"
python -m scripts.seed
uvicorn app.main:app --reload
```

Geometry is stored as GeoJSON for portability across SQLite/PostGIS; the PostGIS path is
documented in `app/models/parcel.py` for when you move spatial filtering into the database.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture and
[`docs/LEGAL.md`](docs/LEGAL.md) for the data-licensing posture that the code enforces.

## Province scope

v1 targets **a single province** (default config: Ontario). Province is a first-class field
on every record and license rules are keyed per province + source, so expanding is a matter
of adding a source adapter and a `DataSourceLicense`, not reworking the model.
