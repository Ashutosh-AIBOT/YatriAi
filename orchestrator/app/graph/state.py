from typing import TypedDict, List, Optional, Dict, Any

class TripState(TypedDict):
    trip_id: str
    user_id: str
    user_prefs: Dict[str, Any]

    # Conversation mode: "chat" or "planning"
    chat_mode: Optional[str]

    # Stage collection
    origin: Optional[str]
    destination: Optional[str]
    trip_type: Optional[str]
    stop_count: Optional[int]
    requested_stops: Optional[List[str]]
    transport_modes: Optional[List[str]]
    start_date: Optional[str]
    end_date: Optional[str]
    total_budget: Optional[float]
    group_size: Optional[int]
    hotel_stars: Optional[int]
    is_vegetarian: Optional[bool]
    cuisine_preferences: Optional[List[str]]
    interest_tags: Optional[List[str]]
    allow_suggestions: Optional[bool]
    current_stage: int

    # Chat history
    messages: List[Dict[str, str]]

    # Agent results
    transport_results: Optional[Dict]
    cab_results: Optional[Dict]
    hotel_results: Optional[Dict]
    food_results: Optional[Dict]
    places_results: Optional[Dict]
    map_results: Optional[Dict]

    # Final plan
    final_plan: Optional[Dict]
    error: Optional[str]
