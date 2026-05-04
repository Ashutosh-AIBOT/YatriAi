"""
Wanderlust Agent — The Travel Motivator

This agent psychologically motivates users to explore and travel.
- Has an intensity slider (0-100): gentle encouragement → strong persuasion
- Auto-interjects in conversations when enabled
- Uses personalization data to tailor messages
- At low intensity: warm, inspiring messages
- At high intensity: challenging, thought-provoking life perspective shifts
"""
import logging
import json
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import settings

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7,  # Higher creativity for motivational content
    groq_api_key=settings.groq_api_key
)

WANDERLUST_PROMPT = """You are the Wanderlust Agent — a travel motivator embedded in Yatri AI.
Your job is to psychologically motivate the user to travel and explore.

INTENSITY LEVEL: {intensity}/100
- 0-30 (Gentle): Be warm, friendly, share beautiful facts about destinations. 
  "Did you know Jaipur's Hawa Mahal has 953 windows? Imagine seeing that sunset..."
- 31-60 (Moderate): Be more persuasive, use FOMO, share life perspectives.
  "Life is short. The best memories aren't made scrolling — they're made exploring."
- 61-80 (Strong): Challenge the user, question their comfort zone.
  "When was the last time you did something for the first time? Your comfort zone is a beautiful prison."
- 81-100 (Maximum): Full philosophical challenge + emotional appeal + urgency.
  "Every day you don't explore is a day you chose routine over wonder. The world won't wait for you."

USER CONTEXT:
- Preferences: {user_prefs}
- Current conversation topic: {topic}
- Destination being discussed: {destination}

RULES:
1. Keep messages SHORT (2-3 sentences max)
2. Be genuine, not salesy
3. Reference specific places/experiences relevant to the conversation
4. At high intensity, mix praise with challenge: "You clearly have great taste — so why settle for the ordinary?"
5. NEVER be rude or offensive — motivate, don't insult
6. If user has dietary preferences, weave in food culture motivation
7. Suggest best time/duration based on the destination
8. Output ONLY the motivational message, nothing else

Generate a single motivational interjection for this moment in the conversation."""


async def motivate(state: dict) -> dict:
    """Generate a wanderlust motivational message based on conversation context."""
    intensity = state.get("wanderlust_intensity", 50)
    
    # Get context from state
    destination = state.get("destination", "somewhere amazing")
    user_prefs = state.get("user_prefs", {})
    prefs_text = user_prefs.get("notes", "") if isinstance(user_prefs, dict) else str(user_prefs)
    
    # Get recent conversation topic
    messages = state.get("messages", [])
    recent_msgs = messages[-3:] if messages else []
    topic = " | ".join([m.get("content", "")[:100] for m in recent_msgs])
    
    if not topic:
        topic = "starting a travel conversation"
    
    try:
        prompt = WANDERLUST_PROMPT.format(
            intensity=intensity,
            user_prefs=prefs_text or "No specific preferences set",
            topic=topic,
            destination=destination or "India"
        )
        
        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"Generate a motivational message at intensity {intensity}/100")
        ])
        
        message = response.content.strip()
        # Clean up any quotes or formatting
        message = message.strip('"\'')
        
        return {
            "wanderlust_message": message,
            "intensity": intensity,
            "destination_suggested": destination,
            "status": "done"
        }
    except Exception as e:
        logger.error(f"Wanderlust agent failed: {e}")
        # Fallback motivational messages by intensity
        fallbacks = {
            (0, 30): f"✨ {destination} has so much to offer. Every journey starts with a single step!",
            (31, 60): f"🌍 Life's too short to stay in one place. {destination} is calling — will you answer?",
            (61, 80): f"🔥 You know what separates dreamers from travelers? A booking confirmation. {destination} won't explore itself.",
            (81, 100): f"⚡ Every sunset you miss in {destination} is a memory that never gets made. The clock is ticking."
        }
        for (low, high), msg in fallbacks.items():
            if low <= intensity <= high:
                return {"wanderlust_message": msg, "intensity": intensity, "status": "fallback"}
        return {"wanderlust_message": f"🌟 {destination} awaits!", "intensity": intensity, "status": "fallback"}


async def suggest_best_places(state: dict) -> dict:
    """Suggest the best places to visit based on user profile, time, and distance."""
    destination = state.get("destination", "")
    origin = state.get("origin", "")
    interests = state.get("interest_tags", [])
    budget = state.get("total_budget", 0)
    duration = state.get("end_date", "")
    user_prefs = state.get("user_prefs", {})
    prefs_text = user_prefs.get("notes", "") if isinstance(user_prefs, dict) else ""
    
    if not destination:
        return {"suggestions": [], "error": "No destination set"}
    
    try:
        prompt = f"""You are a travel expert for India. Based on the traveler's profile:
- Traveling to: {destination}
- From: {origin}  
- Interests: {interests}
- Budget: ₹{budget}
- Duration: {duration}
- Preferences: {prefs_text}

Suggest the TOP 5 must-visit places near {destination}. For each place:
1. Name and why it's perfect for THIS specific person
2. Best time to visit (morning/afternoon/evening)
3. Estimated time needed (hours)
4. Approximate distance from city center
5. Why they should NOT skip it (personalized reason)

Return as JSON array:
[{{"name": "...", "why_perfect": "...", "best_time": "...", "hours_needed": N, "distance_km": N, "must_see_reason": "..."}}]

Return ONLY the JSON array."""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if match:
            suggestions = json.loads(match.group())
            return {"suggestions": suggestions, "error": None}
        else:
            return {"suggestions": [], "error": "Could not parse suggestions", "raw": response.content}
    except Exception as e:
        logger.error(f"Place suggestion failed: {e}")
        return {"suggestions": [
            {"name": f"Heritage Fort in {destination}", "why_perfect": "Matches your love for history", "best_time": "Morning", "hours_needed": 3, "distance_km": 5, "must_see_reason": "Iconic landmark you'll regret missing"},
            {"name": f"Local Food Street in {destination}", "why_perfect": "Perfect for your food preferences", "best_time": "Evening", "hours_needed": 2, "distance_km": 2, "must_see_reason": "Authentic local flavors"},
            {"name": f"Sunset Point {destination}", "why_perfect": "Unforgettable views", "best_time": "Evening", "hours_needed": 1, "distance_km": 8, "must_see_reason": "Best golden hour spot in the region"},
        ], "error": None}
