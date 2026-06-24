"""End-to-end API smoke test through the compliance-enforcing endpoints."""
from __future__ import annotations


def _seed_via_api(client):
    # Ingest public Layer C data through the admin endpoint.
    r = client.post("/api/admin/ingest", params={"province": "ON"})
    assert r.status_code == 200
    assert sum(r.json()["ingested"].values()) > 0


def test_healthz_reports_postal_only(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["electronic_outreach_enabled"] is False


def test_search_and_detail(client):
    _seed_via_api(client)
    r = client.post("/api/search", json={"province": "ON", "distress_types": ["tax_sale"]})
    assert r.status_code == 200
    hits = r.json()
    assert len(hits) >= 1
    pid = hits[0]["parcel"]["id"]

    detail = client.get(f"/api/properties/{pid}").json()
    assert detail["parcel"]["id"] == pid
    assert any(s["signal_type"] == "tax_sale" for s in detail["distress_signals"])


def test_electronic_outreach_is_blocked(client):
    _seed_via_api(client)
    # A contact with no consent.
    from app.db import SessionLocal
    from app.models.outreach import Contact

    s = SessionLocal()
    c = Contact(name="Owner", postal_address="X", email="o@example.com", source_code="demo_title")
    s.add(c)
    s.commit()
    cid = c.id
    s.close()

    camp = client.post("/api/outreach/campaigns", json={"name": "Email blast", "channel": "email"}).json()
    msgs = client.post(f"/api/outreach/campaigns/{camp['id']}/generate", json={"contact_ids": [cid]}).json()
    assert msgs[0]["status"] == "blocked"
    assert "consent" in (msgs[0]["block_reason"] or "").lower() or "disabled" in (msgs[0]["block_reason"] or "").lower()


def test_postal_outreach_is_queued(client):
    _seed_via_api(client)
    from app.db import SessionLocal
    from app.models.outreach import Contact

    s = SessionLocal()
    c = Contact(name="Owner", postal_address="123 Main St", source_code="demo_title")
    s.add(c)
    s.commit()
    cid = c.id
    s.close()

    camp = client.post("/api/outreach/campaigns", json={"name": "Postal", "channel": "postal",
                                                        "template": "Hi {{name}} at {{address}}"}).json()
    msgs = client.post(f"/api/outreach/campaigns/{camp['id']}/generate", json={"contact_ids": [cid]}).json()
    assert msgs[0]["status"] == "queued"
    assert "Owner" in msgs[0]["rendered_body"]
