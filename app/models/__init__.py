"""Model registry. Importing this module registers every table on ``Base.metadata``."""
from app.models.assessment import Assessment
from app.models.comp import Comp
from app.models.distress import DistressSignal
from app.models.instrument import Instrument
from app.models.license import DataSourceLicense
from app.models.outreach import Contact, OutreachCampaign, OutreachMessage
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel
from app.models.property_list import PropertyList, PropertyListItem
from app.models.provenance import ProvenanceRecord
from app.models.user import User

__all__ = [
    "Assessment",
    "Comp",
    "Contact",
    "DataSourceLicense",
    "DistressSignal",
    "Instrument",
    "OutreachCampaign",
    "OutreachMessage",
    "OwnershipRecord",
    "Parcel",
    "PropertyList",
    "PropertyListItem",
    "ProvenanceRecord",
    "User",
]
