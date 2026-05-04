import httpx
import heapq
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)
TIMEOUT = httpx.Timeout(10.0, connect=3.0)

# ─── Indian Transport Network Graph (Dijkstra-ready) ───
# Edges: (city_a, city_b, mode, duration_hrs, price_inr, name)
TRANSPORT_NETWORK = [
    # Northern routes
    ("Delhi", "Jaipur", "train", 4.5, 450, "Shatabdi Express"),
    ("Delhi", "Jaipur", "bus", 5.5, 350, "RSRTC Volvo"),
    ("Delhi", "Jaipur", "flight", 1.0, 3500, "IndiGo 6E-201"),
    ("Delhi", "Agra", "train", 2.0, 350, "Gatimaan Express"),
    ("Delhi", "Agra", "bus", 3.5, 250, "UPSRTC AC"),
    ("Delhi", "Manali", "bus", 12.0, 1200, "HRTC Volvo"),
    ("Delhi", "Manali", "flight", 1.5, 5500, "SpiceJet SG-301 (Kullu)"),
    ("Delhi", "Shimla", "train", 7.0, 600, "Himalayan Queen"),
    ("Delhi", "Shimla", "bus", 8.5, 800, "HRTC Volvo"),
    ("Delhi", "Chandigarh", "train", 3.5, 400, "Shatabdi Express"),
    ("Delhi", "Chandigarh", "bus", 4.5, 500, "Haryana Roadways Volvo"),
    ("Delhi", "Varanasi", "train", 8.0, 800, "Kashi Vishwanath Exp"),
    ("Delhi", "Varanasi", "flight", 1.5, 4000, "Air India AI-433"),
    ("Delhi", "Lucknow", "train", 6.5, 600, "Lucknow Mail"),
    ("Delhi", "Lucknow", "flight", 1.0, 3200, "IndiGo 6E-171"),
    ("Delhi", "Mumbai", "train", 16.0, 1200, "Rajdhani Express"),
    ("Delhi", "Mumbai", "flight", 2.0, 4500, "IndiGo 6E-105"),
    ("Delhi", "Goa", "flight", 2.5, 5000, "SpiceJet SG-461"),
    ("Delhi", "Udaipur", "train", 12.0, 900, "Chetak Express"),
    ("Delhi", "Udaipur", "flight", 1.5, 4200, "IndiGo 6E-481"),
    ("Delhi", "Rishikesh", "bus", 6.0, 600, "UPSRTC Volvo"),
    ("Delhi", "Rishikesh", "train", 5.5, 400, "Dehradun Shatabdi"),
    # Western routes
    ("Mumbai", "Goa", "train", 8.0, 700, "Konkan Kanya Express"),
    ("Mumbai", "Goa", "bus", 10.0, 900, "Neeta Travels Volvo"),
    ("Mumbai", "Goa", "flight", 1.0, 3000, "IndiGo 6E-461"),
    ("Mumbai", "Pune", "train", 3.0, 300, "Deccan Express"),
    ("Mumbai", "Pune", "bus", 3.5, 400, "Shivneri AC"),
    ("Mumbai", "Bangalore", "train", 24.0, 1500, "Udyan Express"),
    ("Mumbai", "Bangalore", "flight", 1.5, 3800, "Vistara UK-851"),
    ("Mumbai", "Jaipur", "train", 12.0, 1000, "Mumbai-Jaipur SF"),
    ("Mumbai", "Jaipur", "flight", 2.0, 4000, "IndiGo 6E-321"),
    # Southern routes
    ("Bangalore", "Chennai", "train", 5.0, 450, "Shatabdi Express"),
    ("Bangalore", "Chennai", "bus", 6.0, 600, "KSRTC Airavat"),
    ("Bangalore", "Chennai", "flight", 1.0, 2800, "IndiGo 6E-801"),
    ("Bangalore", "Goa", "train", 12.0, 800, "Vasco Express"),
    ("Bangalore", "Goa", "bus", 10.0, 1000, "SRS Travels Volvo"),
    ("Bangalore", "Hyderabad", "train", 8.0, 600, "Kachiguda Express"),
    ("Bangalore", "Hyderabad", "flight", 1.0, 3000, "Air India AI-501"),
    # Eastern routes
    ("Kolkata", "Delhi", "train", 17.0, 1300, "Rajdhani Express"),
    ("Kolkata", "Delhi", "flight", 2.0, 4800, "IndiGo 6E-301"),
    ("Kolkata", "Varanasi", "train", 9.0, 700, "Vibhuti Express"),
    # Rajasthan internal
    ("Jaipur", "Udaipur", "train", 6.0, 500, "Chetak Express"),
    ("Jaipur", "Udaipur", "bus", 7.0, 600, "RSRTC Volvo"),
    ("Jaipur", "Jodhpur", "train", 5.0, 400, "Mandore Express"),
    ("Jaipur", "Jodhpur", "bus", 5.5, 500, "RSRTC Volvo"),
    ("Jaipur", "Agra", "train", 3.5, 350, "Marudhar Express"),
    ("Jaipur", "Agra", "bus", 4.0, 400, "RSRTC Express"),
    ("Udaipur", "Jodhpur", "bus", 5.0, 400, "RSRTC Express"),
    # Misc connectors
    ("Chandigarh", "Manali", "bus", 8.0, 700, "HRTC Volvo"),
    ("Chandigarh", "Shimla", "bus", 3.5, 350, "HRTC Volvo"),
    ("Lucknow", "Varanasi", "train", 4.5, 350, "Shatabdi Express"),
    ("Lucknow", "Agra", "train", 3.5, 300, "Gatimaan Express"),
    ("Pune", "Goa", "bus", 8.0, 800, "Paulo Travels AC"),
    ("Pune", "Goa", "train", 7.0, 500, "Goa Express"),
    ("Agra", "Varanasi", "train", 6.0, 500, "Marudhar Express"),
    ("Hyderabad", "Chennai", "train", 7.0, 600, "Charminar Express"),
    ("Hyderabad", "Goa", "flight", 1.0, 3500, "IndiGo 6E-601"),
    # Kanpur connections (user's home city)
    ("Kanpur", "Delhi", "train", 5.0, 500, "Shatabdi Express"),
    ("Kanpur", "Lucknow", "train", 1.5, 150, "Intercity Express"),
    ("Kanpur", "Agra", "train", 3.0, 300, "Kanpur-Agra Express"),
    ("Kanpur", "Varanasi", "train", 5.0, 400, "Kanpur-Varanasi SF"),
    ("Kanpur", "Jaipur", "train", 8.0, 700, "Kanpur-Jaipur SF"),
]


def _build_graph():
    """Build adjacency list from transport network."""
    graph = {}
    for city_a, city_b, mode, duration, price, name in TRANSPORT_NETWORK:
        # Bidirectional
        for src, dst in [(city_a, city_b), (city_b, city_a)]:
            src_l, dst_l = src.lower(), dst.lower()
            if src_l not in graph:
                graph[src_l] = []
            graph[src_l].append({
                "to": dst_l, "to_name": dst, "mode": mode,
                "duration_hrs": duration, "price": price, "name": name
            })
    return graph

GRAPH = _build_graph()


def _find_city(query: str) -> str:
    """Fuzzy match a city name to graph nodes."""
    q = query.lower().strip()
    # Direct match
    if q in GRAPH:
        return q
    # Partial match
    for city in GRAPH:
        if q in city or city in q:
            return city
    return q


def dijkstra_shortest(origin: str, dest: str, optimize: str = "time",
                      budget: float = None, allowed_modes: list = None) -> dict:
    """
    Dijkstra's shortest path for Indian transport network.
    optimize: "time" (fastest) or "cost" (cheapest)
    Returns: { path, total_duration, total_cost, segments }
    """
    src = _find_city(origin)
    dst = _find_city(dest)

    if src not in GRAPH:
        return {"error": f"City '{origin}' not found in transport network", "path": [], "segments": []}
    if dst not in GRAPH:
        return {"error": f"City '{dest}' not found in transport network", "path": [], "segments": []}

    # Priority queue: (cost, duration, city, path, segments)
    # cost is the priority metric
    INF = float('inf')
    if optimize == "time":
        pq = [(0, 0, src, [src], [])]  # (duration, cost, city, path, segments)
    else:
        pq = [(0, 0, src, [src], [])]  # (cost, duration, city, path, segments)

    visited = {}

    while pq:
        primary, secondary, city, path, segments = heapq.heappop(pq)

        if city in visited:
            continue
        visited[city] = True

        if city == dst:
            return {
                "status": "found",
                "path": path,
                "total_duration_hrs": round(primary if optimize == "time" else secondary, 1),
                "total_cost": round(secondary if optimize == "time" else primary),
                "segments": segments,
                "optimize": optimize,
                "stops": len(path) - 2,  # intermediate stops
            }

        for edge in GRAPH.get(city, []):
            next_city = edge["to"]
            if next_city in visited:
                continue

            # Filter by allowed modes
            if allowed_modes and edge["mode"] not in allowed_modes:
                continue

            # Filter by budget
            total_cost_so_far = (secondary if optimize == "time" else primary) + edge["price"]
            if budget and total_cost_so_far > budget:
                continue

            seg = {
                "from": path[-1], "to": edge["to_name"],
                "mode": edge["mode"], "name": edge["name"],
                "duration_hrs": edge["duration_hrs"], "price": edge["price"]
            }

            if optimize == "time":
                new_primary = primary + edge["duration_hrs"]
                new_secondary = secondary + edge["price"]
            else:
                new_primary = primary + edge["price"]
                new_secondary = secondary + edge["duration_hrs"]

            heapq.heappush(pq, (new_primary, new_secondary, next_city,
                                path + [edge["to_name"]], segments + [seg]))

    return {"status": "no_route", "error": f"No route found from {origin} to {dest}", "path": [], "segments": []}


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
    modes = state.get("transport_modes") or ["train", "bus", "flight"]
    trip_type = state.get("trip_type", "explore")  # "urgent" or "explore"
    budget = state.get("total_budget")

    if not origin or not dest:
        return {"routes": [], "fastest_route": None, "cheapest_route": None,
                "error": "Missing origin or destination — please provide both to search routes."}

    cache_key = f"transport:{origin}:{dest}:{date}:{trip_type}"
    if cached := await get_cached(cache_key):
        return cached

    results = {
        "routes": [],
        "fastest_route": None,
        "cheapest_route": None,
        "direct_options": [],
        "error": None,
        "algorithm": "dijkstra_shortest_path"
    }

    # 1. Run Dijkstra for fastest route
    fastest = dijkstra_shortest(origin, dest, optimize="time",
                                budget=budget, allowed_modes=modes)
    if fastest.get("status") == "found":
        results["fastest_route"] = {
            "label": "⚡ Fastest Route",
            "path": " → ".join(fastest["path"]),
            "total_duration": f"{fastest['total_duration_hrs']}h",
            "total_cost": f"₹{fastest['total_cost']}",
            "stops": fastest["stops"],
            "segments": fastest["segments"],
            "recommended": trip_type == "urgent"
        }
        results["routes"].append(results["fastest_route"])

    # 2. Run Dijkstra for cheapest route
    cheapest = dijkstra_shortest(origin, dest, optimize="cost",
                                 budget=budget, allowed_modes=modes)
    if cheapest.get("status") == "found":
        results["cheapest_route"] = {
            "label": "💰 Cheapest Route",
            "path": " → ".join(cheapest["path"]),
            "total_duration": f"{cheapest['total_duration_hrs']}h",
            "total_cost": f"₹{cheapest['total_cost']}",
            "stops": cheapest["stops"],
            "segments": cheapest["segments"],
            "recommended": trip_type == "explore"
        }
        results["routes"].append(results["cheapest_route"])

    # 3. Direct transport options (all modes)
    src_key = _find_city(origin)
    dst_key = _find_city(dest)
    for edge in GRAPH.get(src_key, []):
        if edge["to"] == dst_key:
            if not modes or edge["mode"] in modes:
                results["direct_options"].append({
                    "mode": edge["mode"],
                    "name": edge["name"],
                    "duration": f"{edge['duration_hrs']}h",
                    "price": f"₹{edge['price']}",
                    "price_num": edge["price"],
                    "type": "direct"
                })

    # Sort direct options by price
    results["direct_options"].sort(key=lambda x: x.get("price_num", 0))

    # 4. If trip is urgent, highlight the recommendation
    if trip_type == "urgent" and results["fastest_route"]:
        results["recommendation"] = f"🚨 For your urgent trip, we recommend the fastest route: {results['fastest_route']['path']} ({results['fastest_route']['total_duration']}, {results['fastest_route']['total_cost']})"
    elif results["cheapest_route"]:
        results["recommendation"] = f"💡 For the best value, take: {results['cheapest_route']['path']} ({results['cheapest_route']['total_duration']}, {results['cheapest_route']['total_cost']})"

    await set_cached(cache_key, results, ttl=1800)
    return results


async def get_current_price(alert) -> float:
    """Used by price monitor background task."""
    return alert.get("last_known_price", 0) if isinstance(alert, dict) else getattr(alert, "last_known_price", 0)
