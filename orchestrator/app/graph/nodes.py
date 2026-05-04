from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
import json
import re
import logging
from datetime import datetime, timezone
from .state import TripState
from ..db.crud import save_trip_state, save_chat_message
from ..agents.transport import search as transport_search
from ..agents.cab import compare as cab_compare
from ..agents.hotel import search as hotel_search
from ..agents.food import find as food_find
from ..agents.places import discover as places_discover
from ..agents.maps import build_route as map_route
from ..agents.psychology import analyze_psychology
from ..agents.wanderlust import motivate as wanderlust_motivate, suggest_best_places
from ..agents.base import AgentProtocol
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
- ALWAYS extract any personal information (like their name, where they live, dietary habits, or general likes/dislikes) into `user_prefs_updates` so it can be saved persistently.

== RESPONSE FORMAT ==
Always respond with valid JSON:
{
  "reply": "Your conversational message to the user",
  "extracted": {
    // Only include fields that were mentioned in THIS message
    // e.g. "origin": "Kanpur", "destination": "Noida"
  },
  "user_prefs_updates": "Any newly discovered personal facts (e.g. 'User is named Ashutosh', 'User lives in Kanpur', 'User hates long flights'). Leave empty if none.",
  "ready_to_plan": false,
  "mode": "planning" or "chat"
}

Set ready_to_plan to true ONLY when you have at least: origin, destination, transport_modes, and either budget or dates.
"""

# ─── Single-agent invocation prompt ───

SINGLE_AGENT_PROMPT = """You are Yatri AI. The user wants to use the {agent_name} agent specifically.
Respond helpfully about {agent_topic}. If you need more info, ask for it.
Respond with valid JSON: {{"reply": "your message", "extracted": {{}}, "ready_to_plan": false, "mode": "chat"}}
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

    # Inject user preferences for personalization
    user_prefs = state.get("user_prefs", {})
    prefs_text = user_prefs.get("notes", "") if isinstance(user_prefs, dict) else str(user_prefs)
    if prefs_text:
        history_msgs.append(SystemMessage(
            content=f"USER PERSONAL PREFERENCES (MUST RESPECT): {prefs_text}"
        ))

    # Add mode context
    mode = state.get("chat_mode", "chat")
    if mode == "planning":
        history_msgs.append(SystemMessage(
            content="The user is in TRIP PLANNING mode. Focus on collecting trip information."
        ))

    # Handle single-agent invocation
    target = state.get("target_agent")
    if target:
        agent_topics = {
            "transport": "flights, trains, and buses",
            "cabs": "cab/taxi comparisons (Ola vs Uber)",
            "hotels": "hotel search and recommendations",
            "food": "restaurant and food recommendations",
            "places": "tourist attractions and places to visit",
            "maps": "route planning and directions",
        }
        history_msgs.append(SystemMessage(
            content=SINGLE_AGENT_PROMPT.format(
                agent_name=target,
                agent_topic=agent_topics.get(target, target)
            )
        ))

    # Add recent conversation history (last 10 messages for context)
    recent = messages[-10:]
    for msg in recent:
        if msg["role"] == "user":
            history_msgs.append(HumanMessage(content=msg["content"]))
        else:
            history_msgs.append(SystemMessage(content=f"Your previous reply: {msg['content']}"))

    # Continuous Psychology Profiling (if enabled)
    if state.get("psychology_enabled", True) and not target:
        try:
            from ..agents.psychology import analyze_psychology
            psy_result = await analyze_psychology(state)
            if psy_result.get("status") == "success" and psy_result.get("profile"):
                p = psy_result["profile"]
                state["psychology_results"] = p
                
                psy_prompt = f"PSYCHOLOGICAL PROFILE JUST UPDATED:\n" \
                             f"Mood: {p.get('mood')}\n" \
                             f"Motivation: {p.get('motivation')}\n" \
                             f"Predictive Preferences: {', '.join(p.get('predictive_preferences', []))}\n" \
                             f"Manipulation Hooks (Use these subtly): {', '.join(p.get('manipulation_hooks', []))}\n\n" \
                             f"CRITICAL: Tailor your response and tone to perfectly match this profile."
                history_msgs.insert(-1, SystemMessage(content=psy_prompt))
        except Exception as e:
            logger.warning(f"Continuous psychology analysis failed: {e}")

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
            user_prefs_updates = parsed.get("user_prefs_updates")

            # Update state with any newly extracted info
            safe_keys = {"origin", "destination", "trip_type", "stop_count",
                         "requested_stops", "transport_modes", "start_date",
                         "end_date", "total_budget", "group_size", "hotel_stars",
                         "is_vegetarian", "cuisine_preferences", "interest_tags",
                         "allow_suggestions"}
            for key, value in extracted.items():
                if key in safe_keys and value is not None:
                    state[key] = value
                    
            if user_prefs_updates:
                if "user_prefs" not in state or not isinstance(state["user_prefs"], dict):
                    state["user_prefs"] = {}
                existing_notes = state["user_prefs"].get("notes", "")
                if user_prefs_updates not in existing_notes:
                    state["user_prefs"]["notes"] = f"{existing_notes}\n{user_prefs_updates}".strip()

            # Update mode
            if detected_mode == "planning":
                state["chat_mode"] = "planning"

            # If ready to plan, set stage to trigger agent dispatch
            if ready:
                state["current_stage"] = 8  # Triggers dispatch
                reply_text += "\n\n✨ I have everything I need! Let me activate all my AI agents to create your personalized travel plan..."
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

    # Wanderlust auto-interjection (when enabled)
    if state.get("wanderlust_enabled") and state.get("current_stage", 1) < 8:
        try:
            wl_result = await wanderlust_motivate(state)
            state["wanderlust_results"] = wl_result
            if wl_result.get("wanderlust_message"):
                state["messages"].append({
                    "role": "assistant",
                    "content": f"💫 *Wanderlust says:* {wl_result['wanderlust_message']}"
                })
        except Exception as e:
            logger.warning(f"Wanderlust interjection failed: {e}")

    return state


async def dispatch_agents(state: TripState) -> TripState:
    """
    Run all 6 agents in parallel with full A2A orchestration.
    Each agent reports status and confidence. Agents can read sibling data.
    """
    # Initialize agent statuses
    state["agent_statuses"] = {}
    state["research_pass"] = state.get("research_pass", 0) + 1

    agent_map = {
        "transport": ("transport_results", transport_search),
        "cabs": ("cab_results", cab_compare),
        "hotels": ("hotel_results", hotel_search),
        "food": ("food_results", food_find),
        "places": ("places_results", places_discover),
        "maps": ("map_results", map_route),
        "psychology": ("psychology_results", analyze_psychology),
    }

    # Check if only a single agent is targeted
    target = state.get("target_agent")
    if target and target in agent_map:
        agent_map = {target: agent_map[target]}

    # Mark all agents as "researching"
    for agent_name in agent_map:
        AgentProtocol.set_status(state, agent_name, "researching",
                                 f"Searching for {agent_name} options...")

    # Phase 1: Run all agents in parallel
    async def run_agent(name: str, result_key: str, func):
        """Wrapper that tracks status and computes confidence."""
        try:
            AgentProtocol.set_status(state, name, "researching",
                                     f"Fetching {name} data...")
            result = await func(state)

            # A2A: Some agents can enhance results using sibling data
            called = []
            if name == "food" and AgentProtocol.has_sibling_data(state, "maps"):
                # Food agent can use maps data for location-aware results
                called.append("maps")
            if name == "hotels" and AgentProtocol.has_sibling_data(state, "transport"):
                # Hotel agent can check transport data for arrival times
                called.append("transport")
            if name == "maps" and AgentProtocol.has_sibling_data(state, "places"):
                # Maps can optimize route using places data
                called.append("places")

            confidence = AgentProtocol.calculate_agent_confidence(result, name)
            AgentProtocol.set_status(state, name, "done",
                                     f"{name.title()} research complete",
                                     confidence, called)
            return name, result_key, result
        except Exception as e:
            logger.error(f"Agent {name} failed: {e}")
            AgentProtocol.set_error(state, name, str(e))
            return name, result_key, {"status": "error", "error": str(e), "data": []}

    # Execute all agents concurrently
    tasks = [
        run_agent(name, result_key, func)
        for name, (result_key, func) in agent_map.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Store results
    for item in results:
        if isinstance(item, Exception):
            logger.error(f"Agent task exception: {item}")
            continue
        name, result_key, result = item
        state[result_key] = result

    # Phase 2: Calculate overall confidence
    overall = AgentProtocol.calculate_overall_confidence(state.get("agent_statuses", {}))
    state["overall_confidence"] = round(overall, 1)

    # Phase 3: Re-research if confidence is too low (max 2 passes)
    if state.get("research_pass", 1) < 2 and overall < 40:
        weak = AgentProtocol.needs_reresearch(state.get("agent_statuses", {}))
        if weak:
            logger.info(f"Low confidence ({overall}%). Re-researching: {weak}")
            for agent_name in weak:
                if agent_name in agent_map:
                    AgentProtocol.set_status(state, agent_name, "re-researching",
                                             f"Re-researching {agent_name} for better results...")
            # Re-run weak agents
            re_tasks = [
                run_agent(name, agent_map[name][0], agent_map[name][1])
                for name in weak if name in agent_map
            ]
            re_results = await asyncio.gather(*re_tasks, return_exceptions=True)
            for item in re_results:
                if isinstance(item, Exception):
                    continue
                name, result_key, result = item
                state[result_key] = result

            # Recalculate confidence
            overall = AgentProtocol.calculate_overall_confidence(state.get("agent_statuses", {}))
            state["overall_confidence"] = round(overall, 1)

    return state


async def build_plan(state: TripState) -> TripState:
    """Generate structured itinerary from aggregated agent results using LLM with RAGAS check."""
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
            "user_prefs": state.get("user_prefs", {}),  # Global personalized DOS/DONTS
            "psychology": state.get("psychology_results", {}), # Psychological profile
            "overall_confidence": state.get("overall_confidence", 0),
            "agent_statuses": {
                k: {"status": v.get("status"), "confidence": v.get("confidence")}
                for k, v in (state.get("agent_statuses") or {}).items()
            },
        }

        # Extract user preferences text
        user_prefs = state.get("user_prefs", {})
        prefs_text = user_prefs.get("notes", "") if isinstance(user_prefs, dict) else str(user_prefs)

        plan_prompt = f"""You are the Yatri AI Main Orchestrator Bot. Your 6 subagents have completed their parallel research.
You must now synthesize their data (A2A protocol) into a highly personalized travel plan.

CRITICAL INSTRUCTIONS:
1. You MUST strictly adhere to the user's personal preferences: "{prefs_text}"
2. You MUST use the psychological profile to manipulate and motivate the user effectively: {json.dumps(state.get("psychology_results", {}))}
3. Evaluate how well the plan aligns with preferences → output a confidence_score (0-100)
4. Perform a RAGAS alignment check — rate how relevant, accurate, grounded, and specific the plan is
5. If any agent had low confidence, note it as a caveat in tips
6. Only show information that is RELEVANT to this specific traveler
7. The Main Agent (you) decides what to show and what to hide based on personalization

Agent Research Data: {json.dumps(context, default=str)}

Create a JSON plan with exactly this structure:
{{
  "title": "Trip from X to Y",
  "total_days": N,
  "estimated_cost": N,
  "confidence_score": 85,
  "ragas_alignment_check": "High alignment — plan respects vegetarian preference and budget constraints.",
  "ragas_scores": {{
    "relevance": 0.92,
    "accuracy": 0.88,
    "groundedness": 0.85,
    "personalization": 0.90
  }},
  "agent_contributions": {{
    "transport": "Found 3 train options within budget",
    "hotels": "Selected 3-star hotels per preference",
    "food": "All vegetarian restaurants recommended",
    "places": "Heritage sites matching interest tags",
    "cabs": "Uber vs Ola comparison available",
    "maps": "Optimized route with 2 stops"
  }},
  "days": [
    {{
      "day": 1,
      "activities": [
        {{"time": "9:00 AM", "type": "transport|hotel|food|place", "name": "...", "details": "...", "cost": N}}
      ]
    }}
  ],
  "tips": ["tip1", "tip2"],
  "personalization_notes": "What was customized for this user"
}}

Return ONLY valid JSON. Do not include markdown blocks."""

        response = await llm.ainvoke([HumanMessage(content=plan_prompt)])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            plan = json.loads(match.group())
            state["final_plan"] = plan

            # Store RAGAS result separately for frontend display
            state["ragas_result"] = {
                "alignment": plan.get("ragas_alignment_check", ""),
                "scores": plan.get("ragas_scores", {}),
                "confidence": plan.get("confidence_score", 0),
                "personalization": plan.get("personalization_notes", ""),
            }
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


async def run_single_agent(state: TripState) -> TripState:
    """Run only a single targeted agent (when user clicks an agent directly)."""
    target = state.get("target_agent")
    if not target:
        return state

    agent_map = {
        "transport": ("transport_results", transport_search),
        "cabs": ("cab_results", cab_compare),
        "hotels": ("hotel_results", hotel_search),
        "food": ("food_results", food_find),
        "places": ("places_results", places_discover),
        "maps": ("map_results", map_route),
        "wanderlust": ("wanderlust_results", wanderlust_motivate),
        "psychology": ("psychology_results", analyze_psychology),
    }

    if target not in agent_map:
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": f"I don't have an agent called '{target}'. Available agents: {', '.join(agent_map.keys())}"
        })
        return state

    result_key, func = agent_map[target]
    state["agent_statuses"] = state.get("agent_statuses") or {}
    AgentProtocol.set_status(state, target, "researching", f"Running {target} agent...")

    try:
        result = await func(state)
        confidence = AgentProtocol.calculate_agent_confidence(result, target)
        AgentProtocol.set_status(state, target, "done",
                                 f"{target.title()} search complete", confidence)
        state[result_key] = result
        
        # Append structured output for the user
        if target == "psychology" and result.get("profile"):
            p = result["profile"]
            msg = f"🧠 **Psychological Profile Updated**\n\n" \
                  f"**Mood:** {p.get('mood', 'N/A')}\n" \
                  f"**Motivation:** {p.get('motivation', 'N/A')}\n" \
                  f"**Predictions:** {', '.join(p.get('predictive_preferences', []))}\n" \
                  f"**Hooks:** {', '.join(p.get('manipulation_hooks', []))}\n\n" \
                  f"*Confidence:* {confidence}%"
            state.setdefault("messages", []).append({"role": "assistant", "content": msg})
        elif target == "wanderlust" and result.get("wanderlust_message"):
            state.setdefault("messages", []).append({"role": "assistant", "content": f"💫 *Wanderlust says:* {result['wanderlust_message']}"})
        else:
            state.setdefault("messages", []).append({"role": "assistant", "content": f"✅ **{target.title()} Agent** finished processing successfully. Results have been saved to your profile."})
            
    except Exception as e:
        logger.error(f"Single agent {target} failed: {e}")
        AgentProtocol.set_error(state, target, str(e))
        state[result_key] = {"status": "error", "error": str(e)}
        state.setdefault("messages", []).append({"role": "assistant", "content": f"❌ **{target.title()} Agent** encountered an error: {e}"})

    return state
