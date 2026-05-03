import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_food(dest: str, veg_only: bool, cuisines: list) -> list:
    # Mocking Zomato API call
    results = [
        {"id": "r1", "name": f"Restaurant 1 {dest}", "rating": 4.5, "veg_only": True, "cuisines": ["North Indian"]},
        {"id": "r2", "name": f"Restaurant 2 {dest}", "rating": 4.0, "veg_only": False, "cuisines": ["Chinese", "North Indian"]}
    ]
    if veg_only:
        results = [r for r in results if r["veg_only"]]
    return results

async def find(state: dict) -> dict:
    dest = state.get("destination")
    is_veg = state.get("is_vegetarian", False)
    cuisines = state.get("cuisine_preferences", [])
    
    if not dest:
        return {"restaurants": [], "error": "Missing destination"}

    cache_key = f"food:{dest}:{is_veg}:{','.join(cuisines)}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"restaurants": [], "error": None}

    try:
        results["restaurants"] = await _fetch_food(dest, is_veg, cuisines)
    except Exception as e:
        logger.error(f"Food search failed: {e}")
        results["error"] = f"Food search failed: {e}"

    await set_cached(cache_key, results, ttl=3600)
    return results
