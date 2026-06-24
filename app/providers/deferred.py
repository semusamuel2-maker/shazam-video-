"""Layers D (MLS) and E (skip trace) — DEFERRED for v1.

These layers are intentionally not built. They carry the highest legal/privacy risk and
their absence is a deliberate product decision (spec §4 Layers D & E, §5).

  * Layer D — MLS / sold comps: requires CREA DDF membership and per-board VOW agreements,
    or an aggregator. v1 runs comps off assessment + title sale-history instead
    (``app/services/comps.py``).
  * Layer E — owner contact / skip trace: requires a PIPEDA-licensed data broker and CASL
    consent. v1 does postal outreach to the registered mailing address only.

The functions below exist so that any accidental attempt to use these layers fails loudly
rather than silently doing something non-compliant.
"""
from __future__ import annotations


class DeferredLayerError(NotImplementedError):
    """Raised if code attempts to use a v1-deferred data layer."""


def mls_comps(*_args, **_kwargs):
    raise DeferredLayerError(
        "MLS/sold comps (Layer D) are deferred for v1. Requires CREA DDF + per-board VOW "
        "agreements. Use app/services/comps.py (assessment + sale-history) instead."
    )


def skip_trace(*_args, **_kwargs):
    raise DeferredLayerError(
        "Skip tracing / owner contact (Layer E) is deferred for v1. Requires a "
        "PIPEDA-licensed data broker and CASL consent. Use postal outreach to the "
        "registered mailing address instead."
    )
