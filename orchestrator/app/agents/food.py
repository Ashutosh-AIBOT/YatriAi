import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_food(dest: str, veg_only: bool, cuisines: list) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Using a generic Yelp/Zomato style endpoint structure
        r = await client.get(
            "https://api.yelp.com/v3/businesses/search",
            headers={"Authorization": f"Bearer {settings.zomato_api_key}"},
            params={"location": dest, "term": "restaurants", "limit": 10}
        )
        r.raise_for_status()
        data = r.json()
        
        results = []
        for b in data.get("businesses", []):
            results.append({
                "id": b["id"],
                "name": b["name"],
                "rating": b.get("rating", 0),
                "veg_only": veg_only, # Mocked inference
                "cuisines": [c["title"] for c in b.get("categories", [])]
            })
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
