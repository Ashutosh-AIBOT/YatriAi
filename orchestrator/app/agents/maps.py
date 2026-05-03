import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_route(origin: str, dest: str, stops: list) -> dict:
    # Mocking Google Maps API call
    return {
        "distance": "500 km",
        "duration": "8 hours",
        "polyline": "encoded_polyline_string",
        "waypoints": stops
    }

async def build_route(state: dict) -> dict:
    origin = state.get("origin")
    dest = state.get("destination")
    stops = state.get("requested_stops", [])
    
    if not origin or not dest:
        return {"route": None, "error": "Missing origin or destination"}

    cache_key = f"maps:{origin}:{dest}:{','.join(stops)}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"route": None, "error": None}

    try:
        results["route"] = await _fetch_route(origin, dest, stops)
    except Exception as e:
        logger.error(f"Map route failed: {e}")
        results["error"] = f"Map route failed: {e}"

    await set_cached(cache_key, results, ttl=86400)
    return results
