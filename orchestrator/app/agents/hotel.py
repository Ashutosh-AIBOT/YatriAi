import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_hotels(dest: str, start_date: str, end_date: str, stars: int) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(
            "https://booking-com.p.rapidapi.com/v1/hotels/search",
            headers={
                "X-RapidAPI-Key": settings.rapidapi_key,
                "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
            },
            params={
                "dest_id": dest,
                "search_type": "city",
                "arrival_date": start_date,
                "departure_date": end_date,
                "guest_qty": 1,
                "room_qty": 1
            }
        )
        r.raise_for_status()
        data = r.json()
        
        results = []
        for h in data.get("result", [])[:5]:
            results.append({
                "id": h.get("hotel_id"),
                "name": h.get("hotel_name"),
                "rating": h.get("class", stars),
                "price_per_night": h.get("min_total_price", 0),
                "amenities": ["wifi"] # Mocked due to endpoint limits
            })
        return results

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
