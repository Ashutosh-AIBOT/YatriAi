import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_places(dest: str, tags: list) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        query = f"tourist attractions in {dest} " + " ".join(tags)
        r = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": query,
                "key": settings.google_maps_api_key
            }
        )
        r.raise_for_status()
        data = r.json()
        
        results = []
        for p in data.get("results", [])[:10]:
            results.append({
                "id": p.get("place_id"),
                "name": p.get("name"),
                "type": p.get("types", ["tourist_attraction"])[0],
                "rating": p.get("rating", 0.0)
            })
        return results

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
