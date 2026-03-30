"""API routes for canary SDK callbacks (enterprise feature)."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/canary", tags=["canary"])


@router.post("/")
async def receive_canary(request: Request) -> dict:
    """
    Receive canary test results from the ProbeProxy SDK.
    Stores results in the database for dual-behavior analysis.
    (Implemented in Week 6)
    """
    data = await request.json()
    # TODO: store canary result in DB with source="canary"
    return {"status": "received", "data_keys": list(data.keys())}
