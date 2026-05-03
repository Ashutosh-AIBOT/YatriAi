import asyncio
from ..graph.state import TripState

async def search(state: TripState) -> dict:
    await asyncio.sleep(0.1)
    return {"status": "success", "data": ["flight 1", "train 1"]}
