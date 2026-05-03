from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import asyncio
import json
import re
import logging
from .state import TripState
from ..db.crud import save_trip_state, save_chat_message
from ..agents.transport import search as transport_search
from ..agents.cab import compare as cab_compare
from ..agents.hotel import search as hotel_search
from ..agents.food import find as food_find
from ..agents.places import discover as places_discover
from ..agents.maps import build_route as map_route

logger = logging.getLogger(__name__)

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)

STAGE_QUESTIONS = {
    1: "Welcome to Yatra AI! 🌍 Where would you like to travel from and to? (e.g. Kanpur to Noida)",
    2: "Is this an urgent trip (direct route) or are you looking to explore and enjoy?",
    3: "How would you like to travel? (flight / train / bus / cab / mix)",
    4: "When are you planning to travel, what's your budget, and how many people?",
    5: "Are you vegetarian? Any cuisine preferences? What hotel star rating do you prefer?",
    6: "What kind of places interest you? (forts, nature, food streets, malls, etc.) Should I suggest more places along the way?",
    7: "Perfect! Let me generate your complete travel plan now. One moment... ✨"
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
    """Determine next stage question based on current stage."""
    stage = state["current_stage"]
    if stage > 7:
        return state
    question = STAGE_QUESTIONS.get(stage, "Tell me more about your trip preferences.")
    if stage == 2 and state.get("trip_type") == "explore":
        question = "Great! How many stops would you like, and any specific places you must visit?"
    
    state.setdefault("messages", []).append({"role": "assistant", "content": question})
    try:
        await save_chat_message(state["trip_id"], state["user_id"], "assistant", question, stage)
    except Exception as e:
        logger.warning(f"Could not save chat message: {e}")
    return state

async def extract_stage_info(state: TripState) -> TripState:
    """Use LLM to extract structured info from user's natural language answer."""
    stage = state["current_stage"]
    
    messages = state.get("messages", [])
    if not messages or messages[-1].get("role") != "user":
        return state

    user_input = messages[-1]["content"]
    
    extract_prompt = f"""Extract travel information from user input for stage {stage}.
User said: "{user_input}"
Return JSON with ONLY the fields that are clearly mentioned. 
Stage {stage} fields to extract: {get_stage_fields(stage)}
Return ONLY valid JSON, nothing else."""

    try:
        response = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            extracted = json.loads(match.group())
            # Only update known fields, don't overwrite system fields
            safe_keys = {"origin", "destination", "trip_type", "stop_count", "requested_stops",
                         "transport_modes", "start_date", "end_date", "total_budget", "group_size",
                         "hotel_stars", "is_vegetarian", "cuisine_preferences", "interest_tags",
                         "allow_suggestions"}
            for key, value in extracted.items():
                if key in safe_keys:
                    state[key] = value
    except Exception as e:
        logger.error(f"LLM extraction failed for stage {stage}: {e}")
        # Don't crash — just move to next stage
    
    state["current_stage"] = stage + 1
    try:
        await save_trip_state(state)
    except Exception as e:
        logger.warning(f"Could not save trip state: {e}")
    return state

async def dispatch_agents(state: TripState) -> TripState:
    """Run all 6 agents in parallel — never sequentially. Never crash even if all fail."""
    try:
        results = await asyncio.gather(
            transport_search(state),
            cab_compare(state),
            hotel_search(state),
            food_find(state),
            places_discover(state),
            map_route(state),
            return_exceptions=True
        )
        labels = ["transport_results", "cab_results", "hotel_results",
                  "food_results", "places_results", "map_results"]
        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {label} failed: {result}")
                state[label] = {"status": "error", "error": str(result), "data": []}
            else:
                state[label] = result
    except Exception as e:
        logger.error(f"Agent dispatch entirely failed: {e}")
        state["error"] = f"Agent dispatch failed: {e}"
    return state

async def build_plan(state: TripState) -> TripState:
    """Generate structured itinerary from aggregated agent results using LLM."""
    try:
        # Gather all agent results for context
        context = {
            "origin": state.get("origin"),
            "destination": state.get("destination"),
            "transport": state.get("transport_results", {}),
            "cabs": state.get("cab_results", {}),
            "hotels": state.get("hotel_results", {}),
            "food": state.get("food_results", {}),
            "places": state.get("places_results", {}),
            "route": state.get("map_results", {}),
            "budget": state.get("total_budget"),
            "group_size": state.get("group_size", 1),
            "is_vegetarian": state.get("is_vegetarian"),
            "trip_type": state.get("trip_type"),
        }

        plan_prompt = f"""You are a travel planning AI. Based on the following search results, create a structured day-by-day travel itinerary in JSON format.

Travel Data: {json.dumps(context, default=str)}

Create a JSON plan with this structure:
{{
  "title": "Trip from X to Y",
  "total_days": N,
  "estimated_cost": N,
  "days": [
    {{
      "day": 1,
      "activities": [
        {{"time": "9:00 AM", "type": "transport|hotel|food|place", "name": "...", "details": "...", "cost": N}}
      ]
    }}
  ],
  "tips": ["tip1", "tip2"]
}}

Return ONLY valid JSON."""

        response = await llm.ainvoke([HumanMessage(content=plan_prompt)])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            state["final_plan"] = json.loads(match.group())
        else:
            state["final_plan"] = {"title": f"Trip from {state.get('origin')} to {state.get('destination')}", "raw_response": response.content}
        
        # Add summary message
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": f"🎉 Your travel plan is ready! I've created a detailed itinerary from {state.get('origin')} to {state.get('destination')}."
        })
    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        state["final_plan"] = {
            "title": f"Trip from {state.get('origin')} to {state.get('destination')}",
            "error": str(e),
            "note": "Could not generate full plan, but all search data is available above."
        }
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": "I've gathered all the travel data for your trip! However, I couldn't format the final plan automatically. All individual search results (transport, hotels, food, places) are available."
        })
    return state
