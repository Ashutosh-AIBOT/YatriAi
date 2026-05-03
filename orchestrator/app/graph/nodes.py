from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
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
from ..config import settings

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
    groq_api_key=settings.groq_api_key
)

# ─── System prompt for the conversational travel AI ───

SYSTEM_PROMPT = """You are Yatri AI, a friendly and smart travel planning assistant for India.
You have two modes:
1. GENERAL CHAT — When the user is just chatting, asking questions, or hasn't started planning a trip yet, respond naturally and helpfully. Be warm, knowledgeable, and conversational.
2. TRIP PLANNING — When the user wants to plan a trip (they say "plan a trip", click Plan Trip, or mention travel), you collect information through natural conversation.

== TRIP PLANNING RULES ==
You need to collect the following information for a perfect trip plan. But DO NOT ask all questions at once.
Ask ONE question at a time. Be smart — if the user already mentioned something, acknowledge it and move on.

Required info to collect:
- origin: Where they're traveling from
- destination: Where they're going
- trip_type: "urgent" (direct) or "explore" (leisure, stops allowed)
- transport_modes: How they want to travel (flight/train/bus/cab/mix)
- start_date: When they're going
- end_date: When they're returning (or number of days)
- total_budget: Their budget for the entire trip (in INR)
- group_size: How many people traveling
- hotel_stars: Preferred hotel quality (1-5 stars)
- is_vegetarian: Dietary preference (for food recommendations)
- cuisine_preferences: What kind of food they enjoy
- interest_tags: What they want to see/do (forts, nature, shopping, nightlife, temples, etc.)

== HOW TO ASK ==
- After each user message, extract any info they gave.
- Then ask the NEXT most relevant question naturally.
- If user mentions extra details, acknowledge them ("Great choice! Rajasthan has amazing forts!")
- Combine related questions when natural (e.g. "When are you planning to go, and for how many days?")
- If the user adds info mid-conversation ("also add Jaipur"), acknowledge and update.
- When you have enough info for a good plan, tell the user you're ready to create their plan.

== RESPONSE FORMAT ==
Always respond with valid JSON:
{
  "reply": "Your conversational message to the user",
  "extracted": {
    // Only include fields that were mentioned in THIS message
    // e.g. "origin": "Kanpur", "destination": "Noida"
  },
  "ready_to_plan": false,
  "mode": "planning" or "chat"
}

Set ready_to_plan to true ONLY when you have at least: origin, destination, transport_modes, and either budget or dates.
"""


async def smart_chat(state: TripState) -> TripState:
    """Dynamic conversational AI — replaces the rigid stage system."""
    messages = state.get("messages", [])
    if not messages or messages[-1].get("role") != "user":
        # No new user message — just return welcome
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": "Hey! 👋 I'm Yatri AI, your personal travel companion. You can ask me anything about travel, or tap **Plan Trip** to start planning your next adventure!"
        })
        return state

    user_input = messages[-1]["content"]

    # Build conversation history for context
    history_msgs = [SystemMessage(content=SYSTEM_PROMPT)]

    # Include collected info so AI knows what's already gathered
    collected = {}
    for field in ["origin", "destination", "trip_type", "transport_modes",
                   "start_date", "end_date", "total_budget", "group_size",
                   "hotel_stars", "is_vegetarian", "cuisine_preferences",
                   "interest_tags", "requested_stops"]:
        val = state.get(field)
        if val is not None:
            collected[field] = val

    if collected:
        history_msgs.append(SystemMessage(
            content=f"INFO ALREADY COLLECTED: {json.dumps(collected)}\n"
                    f"Ask the user for the next missing piece of information."
        ))

    # Add mode context
    mode = state.get("chat_mode", "chat")
    if mode == "planning":
        history_msgs.append(SystemMessage(
            content="The user is in TRIP PLANNING mode. Focus on collecting trip information."
        ))

    # Add recent conversation history (last 10 messages for context)
    recent = messages[-10:]
    for msg in recent:
        if msg["role"] == "user":
            history_msgs.append(HumanMessage(content=msg["content"]))
        else:
            history_msgs.append(SystemMessage(content=f"Your previous reply: {msg['content']}"))

    try:
        response = await llm.ainvoke(history_msgs)
        raw = response.content

        # Try to parse JSON response
        parsed = None
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        if parsed:
            reply_text = parsed.get("reply", raw)
            extracted = parsed.get("extracted", {})
            ready = parsed.get("ready_to_plan", False)
            detected_mode = parsed.get("mode", mode)

            # Update state with any newly extracted info
            safe_keys = {"origin", "destination", "trip_type", "stop_count",
                         "requested_stops", "transport_modes", "start_date",
                         "end_date", "total_budget", "group_size", "hotel_stars",
                         "is_vegetarian", "cuisine_preferences", "interest_tags",
                         "allow_suggestions"}
            for key, value in extracted.items():
                if key in safe_keys and value is not None:
                    state[key] = value

            # Update mode
            if detected_mode == "planning":
                state["chat_mode"] = "planning"

            # If ready to plan, set stage to trigger agent dispatch
            if ready:
                state["current_stage"] = 8  # Triggers dispatch
                reply_text += "\n\n✨ I have everything I need! Let me create your personalized travel plan now..."
        else:
            # LLM didn't return JSON — just use the raw text
            reply_text = raw

        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": reply_text
        })

    except Exception as e:
        logger.error(f"Smart chat LLM error: {e}", exc_info=True)
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": "I'm sorry, I had a moment there! 😅 Could you say that again?"
        })

    try:
        await save_chat_message(
            state["trip_id"], state["user_id"], "assistant",
            state["messages"][-1]["content"], state.get("current_stage", 1)
        )
    except Exception as e:
        logger.warning(f"Could not save chat message: {e}")

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
            "interest_tags": state.get("interest_tags"),
            "hotel_stars": state.get("hotel_stars"),
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
            state["final_plan"] = {
                "title": f"Trip from {state.get('origin')} to {state.get('destination')}",
                "raw_response": response.content
            }

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
