import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_hotels(dest: str, start_date: str, end_date: str, stars: int) -> list:
    # Mocking Hotel API call
    return [
        {"id": "h1", "name": f"Hotel 1 {dest}", "rating": stars, "price_per_night": 2000, "amenities": ["wifi", "pool"]},
        {"id": "h2", "name": f"Hotel 2 {dest}", "rating": stars, "price_per_night": 2500, "amenities": ["wifi", "breakfast"]}
    ]

async def search(state: dict) -> dict:
    dest = state.get("destination")
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    stars = state.get("hotel_stars", 3)
    
    if not dest:
        return {"hotels": [], "error": "Missing destination"}

    cache_key = f"hotel:{dest}:{start_date}:{end_date}:{stars}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"hotels": [], "error": None}

    try:
        results["hotels"] = await _fetch_hotels(dest, start_date, end_date, stars)
    except Exception as e:
        logger.error(f"Hotel search failed: {e}")
        results["error"] = f"Hotel search failed: {e}"

    await set_cached(cache_key, results, ttl=3600) # 1 hour cache
    return results
