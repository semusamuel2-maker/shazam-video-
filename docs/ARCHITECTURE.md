# Architecture (v1)

```
                        ┌─────────────────────────────────────────────┐
                        │                Frontend                      │
                        │  frontend/ (MapLibre demo)  →  Next.js (prod)│
                        └───────────────────────┬─────────────────────┘
                                                │ HTTP/JSON
                        ┌───────────────────────▼─────────────────────┐
                        │                FastAPI (app/)                │
                        │  api/properties  api/lists  api/outreach     │
                        │  api/admin (ingest, licenses, PIPEDA)        │
                        └───────┬───────────────┬──────────────┬───────┘
                                │               │              │
              ┌─────────────────▼──┐   ┌────────▼────────┐  ┌──▼───────────────┐
              │  services/          │   │  compliance/    │  │  providers/       │
              │  search, comps,     │◄──┤  license_rules  │  │  title (Layer A)  │
              │  outreach           │   │  casl, pipeda,  │  │  assessment (B)   │
              └─────────┬───────────┘   │  provenance     │  │  deferred (D, E)  │
                        │               └────────┬────────┘  └──────────────────┘
              ┌─────────▼───────────┐            │                (stubbed in v1)
              │  ingestion/ (Layer C)│           │
              │  sources/ + derived  │           │
              └─────────┬───────────┘            │
                        │                        │
              ┌─────────▼────────────────────────▼─────────┐
              │     PostgreSQL + PostGIS  (SQLite in dev)    │
              │  parcels, assessments, ownership, instruments│
              │  distress_signals, comps, lists, outreach,   │
              │  data_source_licenses, provenance_records    │
              └─────────────────────────────────────────────┘
```

## Layered around the moat

Every data record carries a `source_code` that resolves to a `DataSourceLicense`. The
`compliance/` package sits between the services and the data:

- **`license_rules.LicenseEnforcer`** — fail-closed display/export/redistribute/derive
  checks + cache-TTL retention. Search, property detail, and CSV export all pass through it.
- **`casl`** — consent state machine + send gating. Postal is exempt; electronic is gated
  by both consent *and* the `ALLOW_ELECTRONIC_OUTREACH` kill-switch.
- **`pipeda`** — data minimization + access/deletion (DSAR) handling.
- **`provenance`** — append-only audit of where each record came from.

## Data flow (v1, Layer C)

1. `ingestion/sources/*` pull **public** notices (tax sales) → `RawSignal`.
2. `ingestion/base.run_source` upserts parcels, attaches signals idempotently, seeds the
   source's license, writes provenance.
3. `ingestion/derived_signals` computes absentee / long-held from ownership records
   (which, in production, come from the licensed title provider — stubbed in v1).
4. Services read it back through the license enforcer; the API serves only what's permitted.

## Why SQLite *and* PostGIS

The models store geometry as GeoJSON and use a Python-side haversine for radius search, so
the scaffold runs and tests on SQLite with zero setup. In production point `DATABASE_URL`
at PostGIS and move spatial predicates (`ST_DWithin`, `ST_Contains`) into the database — the
seam is documented inline in `app/models/parcel.py` and `app/services/search.py`.

## Extending

- **New public source:** add an `IngestionSource` subclass + register it in
  `ingestion/registry.py`. Give it a `license_seed()`.
- **New licensed feed (once licensed):** implement the matching provider adapter in
  `app/providers/`, tag its data with a `source_code`, add the `DataSourceLicense` row, and
  select it via config. No service/API changes.
- **New province:** set `ACTIVE_PROVINCE`, add the province's sources to the registry, and
  add license rows. Province is a first-class field throughout.
```
