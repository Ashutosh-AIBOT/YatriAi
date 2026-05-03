import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_ola(origin: str, dest: str) -> dict:
    # Mocking Ola API call
    return {"provider": "Ola", "price": 450, "eta": "5 mins", "vehicle_type": "Mini"}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_uber(origin: str, dest: str) -> dict:
    # Mocking Uber API call
    return {"provider": "Uber", "price": 480, "eta": "3 mins", "vehicle_type": "Go"}

async def compare(state: dict) -> dict:
    origin = state.get("origin")
    dest = state.get("destination")
    
    if not origin or not dest:
        return {"options": [], "error": "Missing origin or destination"}

    cache_key = f"cab:{origin}:{dest}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"options": [], "error": None}

    try:
        ola_data = await _fetch_ola(origin, dest)
        results["options"].append(ola_data)
    except Exception as e:
        logger.error(f"Ola search failed: {e}")

    try:
        uber_data = await _fetch_uber(origin, dest)
        results["options"].append(uber_data)
    except Exception as e:
        logger.error(f"Uber search failed: {e}")

    if not results["options"] and not results["error"]:
        results["error"] = "All cab providers failed"

    await set_cached(cache_key, results, ttl=300) # 5 min cache for cabs
    return results
