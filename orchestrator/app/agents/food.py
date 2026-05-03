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
                "veg_only": veg_only,
                "cuisines": [c["title"] for c in b.get("categories", [])]
            })
        return results

async def find(state: dict) -> dict:
    dest = state.get("destination")
    is_veg = state.get("is_vegetarian", False)
    cuisines = state.get("cuisine_preferences") or []
    
    if not dest:
        return {"restaurants": [], "error": "Missing destination"}

    cache_key = f"food:{dest}:{is_veg}:{','.join(str(c) for c in cuisines)}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"restaurants": [], "error": None}

    if settings.is_api_available("zomato_api_key"):
        try:
            results["restaurants"] = await _fetch_food(dest, is_veg, cuisines)
        except Exception as e:
            logger.error(f"Food search failed: {e}")
            results["error"] = f"Food search failed: {e}"
    else:
        # Fallback restaurant data
        veg_tag = "Vegetarian" if is_veg else "Multi-cuisine"
        results["restaurants"] = [
            {"id": "fr1", "name": f"Local Flavors {dest}", "rating": 4.2, "veg_only": is_veg, "cuisines": [veg_tag, "North Indian"]},
            {"id": "fr2", "name": f"Street Food Corner {dest}", "rating": 4.5, "veg_only": is_veg, "cuisines": [veg_tag, "Street Food"]},
            {"id": "fr3", "name": f"Royal Dining {dest}", "rating": 4.0, "veg_only": is_veg, "cuisines": [veg_tag, "Fine Dining"]},
        ]
        results["error"] = "ZOMATO_API_KEY not configured — showing sample restaurants"

    await set_cached(cache_key, results, ttl=3600)
    return results
