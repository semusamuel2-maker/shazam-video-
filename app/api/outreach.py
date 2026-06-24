"""Outreach endpoints. Postal-first; electronic channels gated by CASL."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models.outreach import OutreachCampaign
from app.schemas import CampaignCreate, GenerateMessagesRequest, MessageOut
from app.services.outreach import generate_messages

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


@router.post("/campaigns")
def create_campaign(req: CampaignCreate, session: Session = Depends(get_session)):
    campaign = OutreachCampaign(
        name=req.name,
        channel=req.channel,
        template=req.template,
        owner_user_id=req.owner_user_id,
    )
    session.add(campaign)
    session.commit()
    return {"id": campaign.id, "name": campaign.name, "channel": campaign.channel.value}


@router.post("/campaigns/{campaign_id}/generate", response_model=list[MessageOut])
def generate(campaign_id: int, req: GenerateMessagesRequest, session: Session = Depends(get_session)):
    campaign = session.get(OutreachCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    messages = generate_messages(session, campaign, req.contact_ids)
    return [MessageOut.model_validate(m) for m in messages]
