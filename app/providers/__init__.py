"""Licensed-data providers (spec §4 Layers A/B/D/E).

These are the seams for commercial data. v1 ships **stub** implementations only — they
return nothing and never make network calls. When a data license is signed, implement the
matching adapter (e.g. ``TeranetTitleProvider``) and select it via config; no caller code
changes. Each adapter is responsible for tagging returned data with the correct
``source_code`` so license-rule enforcement applies downstream.
"""
from app.providers.assessment import AssessmentProvider, get_assessment_provider
from app.providers.title import TitleProvider, get_title_provider

__all__ = [
    "AssessmentProvider",
    "TitleProvider",
    "get_assessment_provider",
    "get_title_provider",
]
