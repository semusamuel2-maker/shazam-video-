"""Layer A — Title & ownership provider interface (Teranet / LTSA).

LICENSED DATA. Do not implement a live adapter, and never scrape these sources, until a
commercial license and counsel sign-off are in place (spec §4 Layer A, §2.2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.config import get_settings


@dataclass
class TitleResult:
    owner_name: str | None = None
    mailing_address: str | None = None
    ownership_start: str | None = None  # ISO date
    instruments: list[dict] = field(default_factory=list)
    source_code: str | None = None  # set by the adapter (e.g. "on_teranet")


class TitleProvider(Protocol):
    def lookup(self, parcel_id: str, province: str) -> TitleResult | None: ...


class StubTitleProvider:
    """v1 default. Returns nothing — no licensed title data is available."""

    def lookup(self, parcel_id: str, province: str) -> TitleResult | None:  # noqa: ARG002
        return None


# --- Real adapters go here once licensed. Sketch only; intentionally not wired. ---
#
# class TeranetTitleProvider:
#     """Ontario via Teranet Connect / GeoWarehouse API. source_code='on_teranet'."""
#     def __init__(self, api_key: str): ...
#     def lookup(self, parcel_id, province): ...  # call API, map to TitleResult
#
# class LtsaTitleProvider:
#     """BC via LTSA title search products. source_code='bc_ltsa'."""


def get_title_provider() -> TitleProvider:
    provider = get_settings().title_provider
    if provider == "stub":
        return StubTitleProvider()
    raise NotImplementedError(
        f"Title provider '{provider}' is not implemented. A licensed adapter must be added "
        "before enabling it (see app/providers/title.py)."
    )
