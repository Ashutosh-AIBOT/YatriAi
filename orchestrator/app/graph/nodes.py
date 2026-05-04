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

REQUIRED_PLAN_FIELDS = {
    "origin",
    "destination",
    "group_size",
    "total_budget",
    "trip_type",
    "transport_modes",
}

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
    groq_api_key=settings.groq_api_key
)

# ─── System prompt for the conversational travel AI ───

SYSTEM_PROMPT = """You are Yatri AI, an extremely warm, respectful, and deeply personalized travel planning assistant for India.
You speak like a trusted friend who genuinely cares about the user's travel experience.

== YOUR PERSONALITY ==
- Always greet returning users by name if you know it (from user preferences).
- Reference their known preferences naturally: "Since you love spicy food..." or "I know you prefer budget stays..."
- NEVER be robotic. Be enthusiastic, use emojis sparingly, and make conversations feel alive.
- When the user first clicks "Plan Trip", start with an excited, warm greeting and ask WHERE they want to go.

== TWO MODES ==
1. GENERAL CHAT — Natural conversation. Answer travel questions, share tips, be helpful.
2. TRIP PLANNING — Collect trip info through natural conversation. DO NOT ask all questions at once.

== TRIP PLANNING FLOW (MUST FOLLOW THIS ORDER) ==
When the user wants to plan a trip, collect info in THIS priority order, ONE question at a time:

STEP 1: "Where would you like to go?" (destination) — Ask this FIRST, always.
STEP 2: "Where will you be traveling from?" (origin) — If not known from preferences.
STEP 3: "How many people are traveling?" (group_size)
STEP 4: "What's your budget for this trip?" (total_budget in INR)
STEP 5: "Is this an urgent/direct trip, or do you want to explore along the way?" (trip_type: "urgent" or "explore")
STEP 6: "How would you like to travel — flight, train, bus, or a mix?" (transport_modes)
STEP 7: "When are you planning to go, and for how many days?" (start_date, end_date)
STEP 8: "Any hotel preference — budget, mid-range, or luxury?" (hotel_stars)
STEP 9: "Any food preferences? Vegetarian? Favorite cuisines?" (is_vegetarian, cuisine_preferences)
STEP 10: "What interests you most — forts, nature, shopping, nightlife, temples, adventure?" (interest_tags)

== SMART BEHAVIOR ==
- CHECK USER PREFERENCES FIRST: If you already know their origin, diet, or likes from saved preferences, DON'T re-ask. Say: "I see you usually travel from Kanpur — shall I use that as your starting point?"
- If the user gives multiple pieces of info at once, extract ALL of them and skip to the next unknown.
- Acknowledge every answer enthusiastically before asking the next question.
- If the user seems unsure about budget, suggest ranges: "Most travelers spend ₹15,000-50,000 for a 3-5 day trip."
- When a route preference is detected, note if it's "urgent" (fastest/direct) or "explore" (scenic/flexible).
- ALWAYS extract personal facts into user_prefs_updates to save persistently.

== WHEN TO TRIGGER PLANNING ==
Set ready_to_plan to true ONLY when you have ALL of these:
✅ origin, ✅ destination, ✅ group_size, ✅ total_budget, ✅ trip_type, ✅ transport_modes
When ready, say something like: "Perfect! I have everything I need. Let me activate my 7 AI agents to find the best routes, hotels, food, and experiences for you!"

== RESPONSE FORMAT ==
Always respond with valid JSON:
{
  "reply": "Your warm, personalized conversational message",
  "extracted": {
    // Only include fields mentioned in THIS message
  },
  "user_prefs_updates": "Any newly discovered personal facts. Leave empty string if none.",
  "ready_to_plan": false,
  "mode": "planning" or "chat"
}

CRITICAL RULES:
1. Your ENTIRE response must be a SINGLE valid JSON object. Nothing else.
2. Do NOT include ```json markers, explanations, or any text outside the JSON.
3. Do NOT put the extracted data or ready_to_plan status inside the "reply" text.
4. The "reply" field should ONLY contain the conversational message the user sees.
"""

# ─── Single-agent invocation prompt ───

SINGLE_AGENT_PROMPT = """You are Yatri AI. The user wants to use the {agent_name} agent specifically.
Respond helpfully about {agent_topic}. If you need more info, ask for it.
Respond with valid JSON: {{"reply": "your message", "extracted": {{}}, "ready_to_plan": false, "mode": "chat"}}
"""


def _loads_json_lenient(text: str):
    """Parse JSON with a small cleanup pass for common LLM formatting mistakes."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return json.loads(cleaned)


def _extract_first_json(text: str, expected_type=dict):
    """
    Return the first complete JSON object/array from an LLM response.
    Regex brace matching breaks on nested objects, which is exactly what the
    chat and plan prompts ask the model to produce.
    """
    if not text:
        return None

    try:
        parsed = _loads_json_lenient(text)
        if isinstance(parsed, expected_type):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    starts = "{[" if expected_type is object else ("{" if expected_type is dict else "[")
    for idx, char in enumerate(text):
        if char not in starts:
            continue
        try:
            parsed, _ = decoder.raw_decode(text[idx:])
            if isinstance(parsed, expected_type):
                return parsed
        except json.JSONDecodeError:
            # Try a bounded cleanup from this opening bracket to the last
            # matching closing bracket. This catches trailing commas in objects.
            close = "}" if char == "{" else "]"
            end = text.rfind(close)
            if end > idx:
                try:
                    parsed = _loads_json_lenient(text[idx:end + 1])
                    if isinstance(parsed, expected_type):
                        return parsed
                except json.JSONDecodeError:
                    pass
    return None


def _normalize_extracted(extracted: dict) -> dict:
    """Coerce common LLM field shapes into the state shape the graph expects."""
    if not isinstance(extracted, dict):
        return {}

    normalized = dict(extracted)

    if isinstance(normalized.get("transport_modes"), str):
        normalized["transport_modes"] = [
            mode.strip()
            for mode in re.split(r"[,/]| and ", normalized["transport_modes"])
            if mode.strip()
        ]

    for int_key in ("group_size", "stop_count"):
        value = normalized.get(int_key)
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            if match:
                normalized[int_key] = int(match.group())

    budget = normalized.get("total_budget")
    if isinstance(budget, str):
        match = re.search(r"\d[\d,]*", budget)
        if match:
            normalized["total_budget"] = int(match.group().replace(",", ""))

    return normalized


def _has_required_plan_fields(state: dict) -> bool:
    for field in REQUIRED_PLAN_FIELDS:
        value = state.get(field)
        if value in (None, "", [], {}):
            return False
    return True


def _update_collection_stage(state: dict) -> None:
    """Keep the legacy stage number useful for tests and the frontend."""
    stage = state.get("current_stage", 1)
    if state.get("origin") or state.get("destination"):
        stage = max(stage, 2)
    if state.get("group_size") not in (None, "", [], {}):
        stage = max(stage, 3)
    if state.get("total_budget") not in (None, "", [], {}):
        stage = max(stage, 4)
    if state.get("trip_type") not in (None, "", [], {}):
        stage = max(stage, 5)
    if state.get("transport_modes") not in (None, "", [], {}):
        stage = max(stage, 6)
    if state.get("start_date") or state.get("end_date"):
        stage = max(stage, 7)
    state["current_stage"] = stage


def _summarize_agent_result(agent_name: str, result: dict, confidence: float) -> str:
    """Create a useful chat message for single-agent runs."""
    if not isinstance(result, dict):
        return f"{agent_name.title()} agent finished. Confidence: {confidence}%."

    if result.get("status") == "error":
        return f"{agent_name.title()} agent could not complete: {result.get('error', 'unknown error')}"

    if agent_name == "psychology" and result.get("profile"):
        p = result["profile"]
        predictions = ", ".join(p.get("predictive_preferences", []) or [])
        return (
            "**Psychology Agent** finished.\n\n"
            f"**Mood:** {p.get('mood', 'N/A')}\n"
            f"**Motivation:** {p.get('motivation', 'N/A')}\n"
            f"**Predictions:** {predictions or 'N/A'}\n\n"
            f"Confidence: {confidence}%"
        )

    if agent_name == "wanderlust" and result.get("wanderlust_message"):
        return f"*Wanderlust says:* {result['wanderlust_message']}"

    labels = {
        "transport": ("routes", "route options"),
        "cabs": ("options", "cab options"),
        "hotels": ("hotels", "hotel options"),
        "food": ("restaurants", "food places"),
        "places": ("places", "places"),
        "maps": ("route", "route details"),
    }
    key, label = labels.get(agent_name, ("data", "results"))
    data = result.get(key)

    if isinstance(data, list):
        count = len(data)
        sample = data[0] if data else None
        title = sample.get("name") or sample.get("provider") or sample.get("mode") if isinstance(sample, dict) else None
        suffix = f" Top match: {title}." if title else ""
        return f"**{agent_name.title()} Agent** found {count} {label}.{suffix}\n\nConfidence: {confidence}%"

    if isinstance(data, dict) and data:
        return f"**{agent_name.title()} Agent** prepared {label} for your trip.\n\nConfidence: {confidence}%"

    note = result.get("note") or result.get("error") or "Live data may be unavailable, so fallback data was used where possible."
    return f"**{agent_name.title()} Agent** finished, but had limited data. {note}\n\nConfidence: {confidence}%"


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
            "psychology": "analyzing their travel mood, hidden motivations, and deeply personalizing their upcoming journey. Respond in a very respectful, intuitive, and highly personalized manner.",
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

        # ── Robust JSON parsing ──
        # Strategy 1: Try to find a clean JSON block that contains "reply"
        parsed = None
        reply_text = None
        extracted = {}
        ready = False
        detected_mode = mode
        user_prefs_updates = None

        parsed = _extract_first_json(raw, dict)

        if parsed and "reply" in parsed:
            reply_text = str(parsed["reply"])
            extracted = _normalize_extracted(parsed.get("extracted", {}))
            ready = bool(parsed.get("ready_to_plan", False))
            detected_mode = parsed.get("mode", mode)
            user_prefs_updates = parsed.get("user_prefs_updates")
        elif parsed:
            reply_text = raw
            extracted = _normalize_extracted(parsed.get("extracted", parsed))
            ready = bool(parsed.get("ready_to_plan", False))
            detected_mode = parsed.get("mode", mode)
            user_prefs_updates = parsed.get("user_prefs_updates")
        else:
            # LLM didn't return proper JSON — use raw text but clean it
            reply_text = raw
            
            # Try to detect ready_to_plan from text
            if re.search(r'ready.to.plan.*true', raw, re.IGNORECASE):
                ready = True
            
            # Try to extract fields from embedded JSON blocks
            embedded = re.search(r'"destination"\s*:\s*"([^"]+)"', raw)
            if embedded:
                extracted["destination"] = embedded.group(1)
            embedded = re.search(r'"origin"\s*:\s*"([^"]+)"', raw)
            if embedded:
                extracted["origin"] = embedded.group(1)
            embedded = re.search(r'"group_size"\s*:\s*(\d+)', raw)
            if embedded:
                extracted["group_size"] = int(embedded.group(1))
            embedded = re.search(r'"total_budget"\s*:\s*(\d+)', raw)
            if embedded:
                extracted["total_budget"] = int(embedded.group(1))
            embedded = re.search(r'"trip_type"\s*:\s*"([^"]+)"', raw)
            if embedded:
                extracted["trip_type"] = embedded.group(1)
            embedded = re.search(r'"transport_modes?\s*"\s*:\s*"([^"]+)"', raw)
            if embedded:
                extracted["transport_modes"] = [embedded.group(1)]
            extracted = _normalize_extracted(extracted)

        # ── Always clean reply text of leaked JSON metadata ──
        cleanup_patterns = [
            r'\*\*Extracted:?\*\*[\s\S]*$',
            r'\*\*Ready to [Pp]lan:?\*\*[\s\S]*$',
            r'\*\*Mode:?\*\*[\s\S]*$',
            r'\*\*User [Pp]refs? [Uu]pdates?:?\*\*[\s\S]*$',
            r'\*\*Note:?\*\*[\s\S]*$',
            r'\n\s*\{[^{}]*"(destination|extracted|ready_to_plan|mode)"[^{}]*\}',
        ]
        for pattern in cleanup_patterns:
            reply_text = re.sub(pattern, '', reply_text, flags=re.MULTILINE).strip()
        
        # Remove trailing whitespace and newlines
        reply_text = reply_text.rstrip('\n \t')
        if not reply_text:
            reply_text = "I'm processing your request! What else would you like to share about your trip?"

        # Update state with any newly extracted info
        safe_keys = {"origin", "destination", "trip_type", "stop_count",
                     "requested_stops", "transport_modes", "start_date",
                     "end_date", "total_budget", "group_size", "hotel_stars",
                     "is_vegetarian", "cuisine_preferences", "interest_tags",
                     "allow_suggestions"}
        for key, value in extracted.items():
            if key in safe_keys and value is not None:
                state[key] = value

        _update_collection_stage(state)
                
        if user_prefs_updates and isinstance(user_prefs_updates, str) and user_prefs_updates.strip():
            if "user_prefs" not in state or not isinstance(state["user_prefs"], dict):
                state["user_prefs"] = {}
            existing_notes = state["user_prefs"].get("notes", "")
            if user_prefs_updates not in existing_notes:
                state["user_prefs"]["notes"] = f"{existing_notes}\n{user_prefs_updates}".strip()

        # Update mode
        if detected_mode == "planning":
            state["chat_mode"] = "planning"

        # If ready to plan, set stage to trigger agent dispatch. Also trust the
        # collected state if the model extracted all required fields but forgot
        # to set ready_to_plan=true.
        if ready or _has_required_plan_fields(state):
            state["current_stage"] = 8  # Triggers dispatch
            if "activate" not in reply_text.lower() and "everything i need" not in reply_text.lower():
                reply_text += "\n\n✨ I have everything I need! Let me activate all my AI agents to create your personalized travel plan..."

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

        plan_prompt = f"""You are the Yatri AI Main Orchestrator. Your 7 subagents have completed research.
Synthesize ALL data into a comprehensive, human-friendly travel plan.

USER PREFERENCES: "{prefs_text}"
PSYCHOLOGY PROFILE: {json.dumps(state.get("psychology_results", {}))}
AGENT DATA: {json.dumps(context, default=str)}

== PLAN RULES ==
1. Create a COMPLETE day-by-day chain: Morning breakfast → Place visit → Lunch → Place visit → Evening activity → Dinner → Hotel stay
2. For multi-destination trips, chain cities: City1 (Day 1-2) → Travel → City2 (Day 3-4) → Travel → City3 (Day 5)
3. Every activity MUST have: time, type, name, details, cost, and an "alternatives" array with 1-2 cheaper/better options
4. Each alternative has: name, cost, pros, cons, rating (1-5)
5. Track running budget — show remaining_budget after each day
6. Include transport segments between cities with fastest AND cheapest options
7. Respect dietary preferences, budget limits, and trip_type (urgent=direct routes, explore=scenic)
8. At the end, include a "summary" with totals for transport, food, hotel, activities, and time

Return ONLY valid JSON:
{{
  "title": "Trip: Origin → Destination",
  "total_days": N,
  "estimated_cost": N,
  "budget": N,
  "remaining_budget": N,
  "confidence_score": 85,
  "ragas_alignment_check": "...",
  "ragas_scores": {{"relevance": 0.9, "accuracy": 0.85, "groundedness": 0.8, "personalization": 0.9}},
  "agent_contributions": {{
    "transport": "Found fastest route via train (5h, ₹500)",
    "hotels": "3 budget hotels under ₹1500/night",
    "food": "Vegetarian restaurants prioritized",
    "places": "5 heritage sites matching interests",
    "cabs": "Ola vs Uber at each stop",
    "maps": "Optimized route: A→B→C",
    "psychology": "Adventure-focused plan to match excited mood"
  }},
  "route_chain": ["City A", "City B", "City C"],
  "days": [
    {{
      "day": 1,
      "city": "City Name",
      "theme": "Arrival & Exploration",
      "remaining_budget": N,
      "activities": [
        {{
          "time": "8:00 AM",
          "type": "food",
          "name": "Breakfast at Local Cafe",
          "details": "Famous for masala dosa. Highly rated on Zomato.",
          "cost": 150,
          "why_chosen": "Matches user's love for spicy food and budget preference",
          "alternatives": [
            {{"name": "Hotel Restaurant", "cost": 300, "pros": "Convenient, AC", "cons": "Pricier", "rating": 4}},
            {{"name": "Street Food Stall", "cost": 50, "pros": "Cheapest, authentic", "cons": "No seating", "rating": 3}}
          ]
        }},
        {{
          "time": "10:00 AM",
          "type": "place",
          "name": "Famous Fort",
          "details": "Historic fort with panoramic views. Best visited in the morning.",
          "cost": 50,
          "why_chosen": "Top-rated heritage site matching interest tags",
          "alternatives": []
        }},
        {{
          "time": "1:00 PM",
          "type": "food",
          "name": "Lunch at Spice Garden",
          "details": "Known for authentic local thali.",
          "cost": 200,
          "why_chosen": "Spicy food preference",
          "alternatives": []
        }},
        {{
          "time": "3:00 PM",
          "type": "place",
          "name": "Local Market",
          "details": "Shopping and cultural experience.",
          "cost": 0,
          "why_chosen": "Free activity to balance budget",
          "alternatives": []
        }},
        {{
          "time": "7:00 PM",
          "type": "food",
          "name": "Dinner at Rooftop Restaurant",
          "details": "Great ambiance with city views.",
          "cost": 400,
          "why_chosen": "Highly rated, fits evening vibe",
          "alternatives": []
        }},
        {{
          "time": "9:00 PM",
          "type": "hotel",
          "name": "Budget Hotel Stay",
          "details": "Clean rooms, AC, WiFi. Check-in for the night.",
          "cost": 1200,
          "why_chosen": "Budget preference, 3-star quality",
          "alternatives": [
            {{"name": "Luxury Hotel", "cost": 3500, "pros": "Pool, spa, breakfast", "cons": "Over budget", "rating": 5}},
            {{"name": "Hostel Dorm", "cost": 400, "pros": "Cheapest option", "cons": "Shared room, no privacy", "rating": 2}}
          ]
        }}
      ]
    }}
  ],
  "summary": {{
    "total_transport_cost": N,
    "total_food_cost": N,
    "total_hotel_cost": N,
    "total_activities_cost": N,
    "total_cost": N,
    "total_travel_time_hrs": N,
    "total_stops": N,
    "budget_status": "Under budget by ₹X" or "Over budget by ₹X",
    "key_highlights": ["Highlight 1", "Highlight 2"]
  }},
  "tips": ["tip1", "tip2"],
  "personalization_notes": "Plan customized because user loves spicy food and prefers budget stays"
}}

Return ONLY valid JSON. No markdown."""

        response = await llm.ainvoke([HumanMessage(content=plan_prompt)])
        plan = _extract_first_json(response.content, dict)
        if plan:
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
        
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": _summarize_agent_result(target, result, confidence),
        })
            
    except Exception as e:
        logger.error(f"Single agent {target} failed: {e}")
        AgentProtocol.set_error(state, target, str(e))
        state[result_key] = {"status": "error", "error": str(e)}
        state.setdefault("messages", []).append({"role": "assistant", "content": f"❌ **{target.title()} Agent** encountered an error: {e}"})

    return state
