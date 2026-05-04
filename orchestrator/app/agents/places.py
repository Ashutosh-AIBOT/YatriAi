import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

KNOWN_PLACE_OPTIONS = {
    "agra": [
        {"id": "agra_taj", "name": "Taj Mahal", "type": "monument", "rating": 4.8, "distance_km": 6, "ideal_time": "sunrise or sunset"},
        {"id": "agra_fort", "name": "Agra Fort", "type": "fort", "rating": 4.6, "distance_km": 4, "ideal_time": "late morning"},
        {"id": "mehtab_bagh", "name": "Mehtab Bagh", "type": "garden", "rating": 4.3, "distance_km": 7, "ideal_time": "evening"},
        {"id": "fatehpur_sikri", "name": "Fatehpur Sikri", "type": "heritage", "rating": 4.5, "distance_km": 37, "ideal_time": "half day"},
        {"id": "mathura", "name": "Mathura and Vrindavan", "type": "temple/culture", "rating": 4.5, "distance_km": 58, "ideal_time": "day trip"},
    ],
    "jaipur": [
        {"id": "amber_fort", "name": "Amber Fort", "type": "fort", "rating": 4.7, "distance_km": 11, "ideal_time": "morning"},
        {"id": "city_palace", "name": "City Palace", "type": "palace", "rating": 4.4, "distance_km": 3, "ideal_time": "late morning"},
        {"id": "hawa_mahal", "name": "Hawa Mahal", "type": "landmark", "rating": 4.5, "distance_km": 3, "ideal_time": "morning"},
        {"id": "nahargarh", "name": "Nahargarh Fort", "type": "viewpoint", "rating": 4.5, "distance_km": 8, "ideal_time": "sunset"},
        {"id": "johri_bazar", "name": "Johri Bazaar", "type": "shopping", "rating": 4.3, "distance_km": 2, "ideal_time": "evening"},
    ],
    "varanasi": [
        {"id": "dashashwamedh", "name": "Dashashwamedh Ghat", "type": "ghat", "rating": 4.7, "distance_km": 5, "ideal_time": "evening aarti"},
        {"id": "kashi_vishwanath", "name": "Kashi Vishwanath Temple", "type": "temple", "rating": 4.8, "distance_km": 5, "ideal_time": "early morning"},
        {"id": "sarnath", "name": "Sarnath", "type": "heritage", "rating": 4.5, "distance_km": 10, "ideal_time": "half day"},
    ],
}

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
    tags = state.get("interest_tags") or []
    
    if not dest:
        return {"places": [], "error": "Missing destination"}

    tag_str = ",".join(str(t) for t in tags)
    cache_key = f"places:{dest}:{tag_str}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"places": [], "error": None}

    if settings.is_api_available("google_maps_api_key"):
        try:
            results["places"] = await _fetch_places(dest, tags)
        except Exception as e:
            logger.error(f"Places search failed: {e}")
            results["error"] = f"Places search failed: {e}"
    else:
        # Fallback places data
        known_key = next((key for key in KNOWN_PLACE_OPTIONS if key in dest.lower()), None)
        results["places"] = KNOWN_PLACE_OPTIONS.get(known_key, [
            {"id": "fp1", "name": f"Heritage Fort in {dest}", "type": "tourist_attraction", "rating": 4.5, "distance_km": 8},
            {"id": "fp2", "name": f"City Garden {dest}", "type": "park", "rating": 4.2, "distance_km": 5},
            {"id": "fp3", "name": f"Local Market {dest}", "type": "shopping_mall", "rating": 4.0, "distance_km": 3},
            {"id": "fp4", "name": f"Historical Museum {dest}", "type": "museum", "rating": 4.3, "distance_km": 6},
        ])
        results["error"] = "GOOGLE_MAPS_API_KEY not configured — showing sample places"

    await set_cached(cache_key, results, ttl=86400)
    return results
