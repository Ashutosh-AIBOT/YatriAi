import asyncio
from ..graph.state import TripState

async def build_route(state: TripState) -> dict:
    await asyncio.sleep(0.1)
    return {"status": "success", "data": ["map route"]}
