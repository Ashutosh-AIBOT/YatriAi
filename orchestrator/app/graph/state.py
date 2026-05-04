from typing import TypedDict, List, Optional, Dict, Any


class AgentStatus(TypedDict, total=False):
    """Status of a single sub-agent."""
    status: str          # "idle" | "researching" | "done" | "error" | "re-researching"
    message: str         # Human-readable status message
    confidence: float    # 0-100, how confident this agent is in its results
    started_at: Optional[str]
    finished_at: Optional[str]
    data: Optional[Any]  # The agent's raw result data
    error: Optional[str]
    called_agents: Optional[List[str]]  # A2A: which other agents this one consulted


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

    # ─── Agent Orchestration (NEW) ───
    agent_statuses: Optional[Dict[str, AgentStatus]]
    overall_confidence: Optional[float]     # 0-100 aggregated
    ragas_result: Optional[Dict[str, Any]]  # RAGAS alignment check result
    research_pass: Optional[int]            # Which pass of research (1=first, 2=re-research)
    target_agent: Optional[str]             # If set, only run this single agent

    # ─── Wanderlust Motivator Agent ───
    wanderlust_enabled: Optional[bool]       # Toggle on/off
    wanderlust_intensity: Optional[int]      # 0-100 intensity slider
    wanderlust_results: Optional[Dict]       # Latest motivational message

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
