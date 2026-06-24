"""License-rule enforcement.

Every record carries a ``source_code``. Before the app displays, exports, or redistributes
a record it asks this module whether the governing :class:`DataSourceLicense` permits it.
Unknown sources are denied (fail closed) — you cannot accidentally surface data from a
source you have not explicitly licensed.
"""
from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.license import DataSourceLicense


class LicenseAction(str, enum.Enum):
    DISPLAY = "display"
    EXPORT = "export"
    REDISTRIBUTE = "redistribute"
    DERIVE = "derive"


class LicenseViolation(Exception):
    """Raised when an action is attempted that the source's license does not permit."""

    def __init__(self, source_code: str, action: LicenseAction, reason: str):
        self.source_code = source_code
        self.action = action
        self.reason = reason
        super().__init__(f"License denies {action.value} for source '{source_code}': {reason}")


_ATTR = {
    LicenseAction.DISPLAY: "can_display",
    LicenseAction.EXPORT: "can_export",
    LicenseAction.REDISTRIBUTE: "can_redistribute",
    LicenseAction.DERIVE: "can_derive",
}


class LicenseEnforcer:
    """Resolves source codes to license rows (cached) and answers permission questions."""

    def __init__(self, session: Session):
        self._session = session
        self._cache: dict[str, DataSourceLicense | None] = {}

    def _license(self, source_code: str | None) -> DataSourceLicense | None:
        if not source_code:
            return None
        if source_code not in self._cache:
            self._cache[source_code] = self._session.scalar(
                select(DataSourceLicense).where(DataSourceLicense.code == source_code)
            )
        return self._cache[source_code]

    def is_allowed(self, source_code: str | None, action: LicenseAction) -> bool:
        lic = self._license(source_code)
        if lic is None:
            return False  # fail closed: unknown source => no rights
        return bool(getattr(lic, _ATTR[action]))

    def require(self, source_code: str | None, action: LicenseAction) -> None:
        if not self.is_allowed(source_code, action):
            lic = self._license(source_code)
            reason = "no license on file for source" if lic is None else "right not granted"
            raise LicenseViolation(source_code or "<none>", action, reason)

    def filter_displayable(self, rows: list) -> list:
        """Drop rows whose source does not permit display. Rows must have ``source_code``."""
        return [r for r in rows if self.is_allowed(getattr(r, "source_code", None), LicenseAction.DISPLAY)]

    def is_within_cache_ttl(self, source_code: str | None, retrieved_at: datetime) -> bool:
        """True if a record retrieved at ``retrieved_at`` is still within its cache TTL."""
        lic = self._license(source_code)
        if lic is None or lic.cache_ttl_days is None:
            return True  # open/public data or no limit
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - retrieved_at <= timedelta(days=lic.cache_ttl_days)
