import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

async def _get_amadeus_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.amadeus_client_id,
            "client_secret": settings.amadeus_client_secret
        }
    )
    r.raise_for_status()
    return r.json().get("access_token")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_flights(origin: str, dest: str, date: str) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        token = await _get_amadeus_token(client)
        r = await client.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={"originLocationCode": origin, "destinationLocationCode": dest,
                    "departureDate": date, "adults": 1, "max": 5}
        )
        r.raise_for_status()
        return r.json().get("data", [])

async def search(state: dict) -> dict:
    origin = state.get("origin")
    dest = state.get("destination")
    date = state.get("start_date", "")
    modes = state.get("transport_modes", ["train", "bus"])

    if not origin or not dest:
        return {"flights": [], "trains": [], "buses": [], "error": "Missing origin or destination"}

    # Format dates or codes if needed (assuming origin/dest are IATA codes for flights)
    cache_key = f"transport:{origin}:{dest}:{date}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"flights": [], "trains": [], "buses": [], "error": None}

    try:
        if "flight" in modes:
            results["flights"] = await _fetch_flights(origin, dest, date)
    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        results["error"] = f"Flight search failed: {e}"
        results["flights"] = []

    # Train and bus logic placeholder
    if "train" in modes:
        results["trains"] = [{"id": "train1", "price": 1000, "duration": "10h"}]
    if "bus" in modes:
        results["buses"] = [{"id": "bus1", "price": 800, "duration": "12h"}]

    await set_cached(cache_key, results, ttl=1800)
    return results

async def get_current_price(alert) -> float:
    # Used by price monitor
    return alert.last_known_price
