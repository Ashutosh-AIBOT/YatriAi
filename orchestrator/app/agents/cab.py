import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_ola(origin: str, dest: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(
            "https://devapi.olacabs.com/v1/products",
            headers={"X-APP-TOKEN": settings.ola_api_key},
            params={"pickup_lat": origin.split(',')[0], "pickup_lng": origin.split(',')[1]}
        )
        r.raise_for_status()
        data = r.json()
        return {"provider": "Ola", "price": data.get("categories", [{}])[0].get("fare_info", {}).get("minimum_fare", 0), "eta": "5 mins", "vehicle_type": "Mini"}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_uber(origin: str, dest: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(
            "https://api.uber.com/v1.2/estimates/price",
            headers={"Authorization": f"Token {settings.uber_server_token}"},
            params={
                "start_latitude": origin.split(',')[0], "start_longitude": origin.split(',')[1],
                "end_latitude": dest.split(',')[0], "end_longitude": dest.split(',')[1]
            }
        )
        r.raise_for_status()
        data = r.json()
        price_estimate = data.get("prices", [{}])[0]
        return {"provider": "Uber", "price": price_estimate.get("high_estimate", 0), "eta": "3 mins", "vehicle_type": price_estimate.get("display_name", "Go")}

async def compare(state: dict) -> dict:
    origin = state.get("origin")
    dest = state.get("destination")
    
    if not origin or not dest:
        return {"options": [], "error": "Missing origin or destination"}

    cache_key = f"cab:{origin}:{dest}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"options": [], "error": None}

    # Ola — only if API key is configured
    if settings.is_api_available("ola_api_key"):
        try:
            ola_data = await _fetch_ola(origin, dest)
            results["options"].append(ola_data)
        except Exception as e:
            logger.error(f"Ola search failed: {e}")
    else:
        results["options"].append({"provider": "Ola", "price": "N/A", "eta": "~8 mins", "vehicle_type": "Mini", "note": "OLA_API_KEY not configured"})

    # Uber — only if API key is configured
    if settings.is_api_available("uber_server_token"):
        try:
            uber_data = await _fetch_uber(origin, dest)
            results["options"].append(uber_data)
        except Exception as e:
            logger.error(f"Uber search failed: {e}")
    else:
        results["options"].append({"provider": "Uber", "price": "N/A", "eta": "~5 mins", "vehicle_type": "Go", "note": "UBER_SERVER_TOKEN not configured"})

    await set_cached(cache_key, results, ttl=300)  # 5 min cache for cabs
    return results
