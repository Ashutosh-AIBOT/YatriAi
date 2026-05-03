from ..graph.state import TripState

async def merge(state: TripState) -> dict:
    return {
        "transport": state.get("transport_results"),
        "cab": state.get("cab_results"),
        "hotel": state.get("hotel_results")
    }

async def rank_by_preferences(aggregated: dict, prefs: dict) -> dict:
    return aggregated
