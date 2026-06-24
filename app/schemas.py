"""Pydantic request/response models for the API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.enums import DistressType, OutreachChannel, OwnerType


class ParcelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    parcel_id: str
    province: str
    municipality: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class DistressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    signal_type: DistressType
    confidence: float
    detail: str | None = None
    source_code: str | None = None
    published_date: str | None = None


class SearchHitOut(BaseModel):
    parcel: ParcelOut
    distress_types: list[str]
    assessed_value: float | None = None
    owner_type: str | None = None


class SearchRequest(BaseModel):
    province: str | None = None
    municipality: str | None = None
    distress_types: list[DistressType] | None = None
    owner_type: OwnerType | None = None
    min_value: float | None = None
    max_value: float | None = None
    property_class: str | None = None
    min_years_held: int | None = None
    center_lat: float | None = None
    center_lon: float | None = None
    radius_km: float | None = None
    limit: int = 100


class CompOut(BaseModel):
    estimated_value: float | None
    low: float | None
    high: float | None
    method: str
    comparable_count: int


class PropertyDetailOut(BaseModel):
    parcel: ParcelOut
    assessment: dict | None = None
    ownership: dict | None = None
    instruments: list[dict] = []
    distress_signals: list[DistressOut] = []
    comp: CompOut | None = None


class ListCreate(BaseModel):
    name: str
    owner_user_id: int | None = None


class ListItemCreate(BaseModel):
    parcel_id: int
    note: str | None = None


class CampaignCreate(BaseModel):
    name: str
    channel: OutreachChannel = OutreachChannel.POSTAL
    template: str | None = None
    owner_user_id: int | None = None


class GenerateMessagesRequest(BaseModel):
    contact_ids: list[int]


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contact_id: int
    channel: OutreachChannel
    status: str
    block_reason: str | None = None
    rendered_body: str | None = None
