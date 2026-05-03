from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import asyncio
from .state import TripState
import json
import re
from ..db.crud import save_trip_state, save_chat_message
from ..agents.transport import search as transport_search
from ..agents.cab import compare as cab_compare
from ..agents.hotel import search as hotel_search
from ..agents.food import find as food_find
from ..agents.places import discover as places_discover
from ..agents.maps import build_route as map_route

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)

STAGE_QUESTIONS = {
    1: "Where would you like to travel from and to? (e.g. Kanpur to Noida)",
    2: "Is this an urgent trip (direct route) or are you looking to explore and enjoy?",
    3: "How would you like to travel? (flight / train / bus / cab / mix)",
    4: "When are you planning to travel, what's your budget, and how many people?",
    5: "Are you vegetarian? Any cuisine preferences? What hotel star rating do you prefer?",
    6: "What kind of places interest you? (forts, nature, food streets, malls, etc.) Should I suggest more places along the way?",
    7: "Perfect! Let me generate your complete travel plan now. One moment..."
}

def get_stage_fields(stage: int) -> str:
    fields = {
        1: "origin (str), destination (str)",
        2: "trip_type (urgent|explore), stop_count (int), requested_stops (list)",
        3: "transport_modes (list of: flight|train|bus|cab)",
        4: "start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), total_budget (float), group_size (int)",
        5: "is_vegetarian (bool), cuisine_preferences (list), hotel_stars (int 1-5)",
        6: "interest_tags (list), allow_suggestions (bool)",
        7: ""
    }
    return fields.get(stage, "")


async def stage_router(state: TripState) -> TripState:
    stage = state["current_stage"]
    if stage > 7:
        return state
    question = STAGE_QUESTIONS[stage]
    if stage == 2 and state.get("trip_type") == "explore":
        question = "Great! How many stops would you like, and any specific places you must visit?"
    
    state.setdefault("messages", []).append({"role": "assistant", "content": question})
    await save_chat_message(state["trip_id"], state["user_id"], "assistant", question, stage)
    return state

async def extract_stage_info(state: TripState) -> TripState:
    stage = state["current_stage"]
    
    # We expect user's last message to be the one we extract from
    messages = state.get("messages", [])
    if not messages or messages[-1]["role"] != "user":
        return state # no user input to process
        
    user_input = messages[-1]["content"]
    
    extract_prompt = f"""
Extract travel information from user input for stage {stage}.
Current state: {state}
User said: "{user_input}"
Return JSON with ONLY the fields that are clearly mentioned. 
Stage {stage} fields to extract: {get_stage_fields(stage)}
Return ONLY valid JSON, nothing else.
"""
    try:
        response = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            extracted = json.loads(match.group())
            state.update(extracted)
    except Exception:
        pass
        
    state["current_stage"] = stage + 1
    await save_trip_state(state)
    return state

async def dispatch_agents(state: TripState) -> TripState:
    results = await asyncio.gather(
        transport_search(state),
        cab_compare(state),
        hotel_search(state),
        food_find(state),
        places_discover(state),
        map_route(state),
        return_exceptions=True
    )
    state["transport_results"] = results[0] if not isinstance(results[0], Exception) else {"status": "error"}
    state["cab_results"] = results[1] if not isinstance(results[1], Exception) else {"status": "error"}
    state["hotel_results"] = results[2] if not isinstance(results[2], Exception) else {"status": "error"}
    state["food_results"] = results[3] if not isinstance(results[3], Exception) else {"status": "error"}
    state["places_results"] = results[4] if not isinstance(results[4], Exception) else {"status": "error"}
    state["map_results"] = results[5] if not isinstance(results[5], Exception) else {"status": "error"}
    return state

async def build_plan(state: TripState) -> TripState:
    state["final_plan"] = {"plan": "Your awesome trip!"}
    return state
