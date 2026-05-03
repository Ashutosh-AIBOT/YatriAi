import asyncio
from ..graph.state import TripState

async def discover(state: TripState) -> dict:
    await asyncio.sleep(0.1)
    return {"status": "success", "data": ["place a", "place b"]}
