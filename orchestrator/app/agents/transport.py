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
    modes = state.get("transport_modes") or ["train", "bus"]

    if not origin or not dest:
        return {"flights": [], "trains": [], "buses": [], "error": "Missing origin or destination"}

    cache_key = f"transport:{origin}:{dest}:{date}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"flights": [], "trains": [], "buses": [], "error": None}

    # Flights — only if API key is configured
    if "flight" in modes:
        if settings.is_api_available("amadeus_client_id"):
            try:
                results["flights"] = await _fetch_flights(origin, dest, date)
            except Exception as e:
                logger.error(f"Flight search failed: {e}")
                results["flights"] = [{"id": "fallback", "note": "Flight API unavailable, please check manually", "origin": origin, "destination": dest}]
        else:
            results["flights"] = [{"id": "no-api", "note": "Amadeus API key not configured. Add AMADEUS_CLIENT_ID to enable live flights.", "origin": origin, "destination": dest}]

    # Train/Bus — fallback data (no external API needed)
    if "train" in modes:
        results["trains"] = [{"id": "train1", "name": f"{origin} → {dest} Express", "price": 800, "duration": "8h", "class": "Sleeper"}]
    if "bus" in modes:
        results["buses"] = [{"id": "bus1", "name": f"{origin} → {dest} Volvo", "price": 600, "duration": "10h", "type": "AC Sleeper"}]

    await set_cached(cache_key, results, ttl=1800)
    return results

async def get_current_price(alert) -> float:
    """Used by price monitor background task."""
    return alert.get("last_known_price", 0) if isinstance(alert, dict) else getattr(alert, "last_known_price", 0)
