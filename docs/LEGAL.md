# Legal & data-licensing posture

> This document describes how the code reflects the build spec's legal strategy. It is **not
> legal advice.** Retain a Canadian real estate data + privacy lawyer before going to
> production, and verify every provider's current terms directly.

## The core rule the code enforces

**Only public / openly-licensed data is ingested. Licensed commercial datasets are accessed
only through signed agreements + APIs — never scraped.**

The repo contains **no scrapers for, and no live integrations with**, Teranet, LTSA, MPAC,
BC Assessment, or any MLS/board system. Those are licensed commercial datasets; scraping
them would breach their terms and undermine the entire strategy (the moat *is* the
licensing). They are represented only as **provider interfaces** (`app/providers/`) with
stub implementations that return nothing.

## Data layers and their status in this repo

| Layer | Data | Status in v1 | How it's accessed |
|-------|------|--------------|-------------------|
| A — Title/ownership | owner, instruments, sale history | **stubbed** | commercial license + API (Teranet / LTSA) — not wired |
| B — Assessment | assessed value, characteristics | **stubbed** | licensed (MPAC / BC Assessment) or municipal open data |
| C — Distress signals | tax sales, power of sale, probate, liens, absentee, long-held | **built** | public notices (ingested) + derived from licensed layers |
| D — MLS / comps | active + sold listings | **deferred** | CREA DDF + per-board VOW — `providers/deferred.py` raises |
| E — Owner contact | phone, email | **deferred** | PIPEDA-licensed broker only — `providers/deferred.py` raises |

## How each statute is reflected in code

**License terms (per source).** `DataSourceLicense` stores enforceable rights — display,
export, redistribute, derive, and `cache_ttl_days`. `LicenseEnforcer` checks them and
**fails closed** for unknown sources. Defaults deny; you open rights per signed agreement.

**PIPEDA.** `compliance/pipeda.py` enforces data minimization (v1 stores only name +
registered mailing address — no phone/email), and implements access (DSAR) and deletion
requests, surfaced at `/api/admin/pipeda/*`.

**CASL.** `compliance/casl.py` is a consent state machine. Postal mail is not a commercial
electronic message and is always allowed. Email/SMS require express/implied consent, an
unsubscribe + sender ID in the template, and are additionally gated by the
`ALLOW_ELECTRONIC_OUTREACH` kill-switch — **v1 stays postal-only.** `WITHDRAWN` is terminal.

**Audit trail.** `ProvenanceRecord` logs the source and time of every ingested/derived
record so compliance is provable.

## Before production — checklist (spec §10, §11)

- [ ] Retain Canadian real estate data + privacy counsel.
- [ ] Confirm Layer A + B licensing terms for the launch province (redistribution, caching,
      derived-data rights). Encode them as `DataSourceLicense` rows.
- [ ] Decide MLS in/out for v1 (recommended: **out**).
- [ ] Confirm which municipalities publish usable **open** assessment/parcel data and their
      licence terms before adding those adapters.
- [ ] Set per-source `cache_ttl_days` to match each agreement; add a retention sweep job.
- [ ] Review the CASL consent-capture flow with counsel before flipping
      `ALLOW_ELECTRONIC_OUTREACH`.
- [ ] Publish a privacy policy; define the lawful basis and DSAR process operationally.

## ⚠️ Do not

- Do not implement a provider adapter against a licensed source without a signed license.
- Do not enable electronic outreach without counsel sign-off on consent capture.
- Do not relax a `DataSourceLicense` default beyond what the signed agreement grants.
- Do not ingest any source not represented by a `DataSourceLicense` row — it will be denied
  display anyway (fail-closed), but don't rely on that as a substitute for diligence.
