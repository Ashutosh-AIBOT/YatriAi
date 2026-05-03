import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_places(dest: str, tags: list) -> list:
    # Mocking Places API call
    return [
        {"id": "p1", "name": f"Place 1 {dest}", "type": "monument", "rating": 4.8},
        {"id": "p2", "name": f"Place 2 {dest}", "type": "park", "rating": 4.5}
    ]

async def discover(state: dict) -> dict:
    dest = state.get("destination")
    tags = state.get("interest_tags", [])
    
    if not dest:
        return {"places": [], "error": "Missing destination"}

    cache_key = f"places:{dest}:{','.join(tags)}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"places": [], "error": None}

    try:
        results["places"] = await _fetch_places(dest, tags)
    except Exception as e:
        logger.error(f"Places search failed: {e}")
        results["error"] = f"Places search failed: {e}"

    await set_cached(cache_key, results, ttl=86400) # 24 hour cache
    return results
