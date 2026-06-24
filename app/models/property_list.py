"""List + membership — user-saved target lists of parcels."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PropertyList(Base):
    __tablename__ = "property_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["PropertyListItem"]] = relationship(
        back_populates="property_list", cascade="all, delete-orphan"
    )


class PropertyListItem(Base):
    __tablename__ = "property_list_items"
    __table_args__ = (UniqueConstraint("list_id", "parcel_id", name="uq_list_parcel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("property_lists.id"), index=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)
    note: Mapped[str | None] = mapped_column(String(512))

    property_list: Mapped["PropertyList"] = relationship(back_populates="items")
