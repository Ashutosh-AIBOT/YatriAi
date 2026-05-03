from ..rag.ranker import rank

async def merge(state: dict) -> dict:
    return {
        "transport": state.get("transport_results"),
        "cab": state.get("cab_results"),
        "hotel": state.get("hotel_results"),
        "food": state.get("food_results"),
        "places": state.get("places_results"),
        "map": state.get("map_results")
    }

async def rank_by_preferences(aggregated: dict, user_prefs: dict) -> dict:
    return await rank(aggregated, user_prefs)
