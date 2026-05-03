import asyncio
from ..graph.state import TripState

async def find(state: TripState) -> dict:
    await asyncio.sleep(0.1)
    return {"status": "success", "data": ["restaurant 1", "cafe 2"]}
