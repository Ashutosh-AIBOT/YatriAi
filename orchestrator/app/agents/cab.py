import asyncio
from ..graph.state import TripState

async def compare(state: TripState) -> dict:
    await asyncio.sleep(0.1)
    return {"status": "success", "data": ["ola cab", "uber cab"]}
