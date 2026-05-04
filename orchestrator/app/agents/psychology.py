import json
import logging
from typing import Dict, Any
from .base import AgentProtocol
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ..config import settings

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7,
    groq_api_key=settings.groq_api_key
)

async def analyze_psychology(state: dict) -> Dict[str, Any]:
    """
    Psychology Agent: Analyzes user's mood, travel motivations, and manipulates/predicts preferences.
    Saves in a structured format.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"status": "skipped", "message": "No messages to analyze"}

    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    if not user_msgs:
        return {"status": "skipped", "message": "No user messages to analyze"}

    # Extract last few messages for recent mood, and all for general profile
    recent_msgs = user_msgs[-3:]
    all_msgs = "\n".join(user_msgs)

    prompt = f"""You are the Yatri AI Psychology & Personalization Agent.
Your job is to analyze the user's chat history and extract their deep psychological travel profile.
Do not extract basic trip details (like origin/destination). Focus on:
1. "mood": The user's current emotional state (e.g., stressed, excited, tired, looking for adventure).
2. "motivation": Why they are traveling (e.g., escape from work, cultural immersion, family bonding).
3. "predictive_preferences": What they might like based on their tone (e.g., quiet places, nightlife, luxury, budget-conscious).
4. "manipulation_hooks": What kind of language or suggestions will motivate them best (e.g., "FOMO", "relaxation", "status/luxury", "hidden gems").

User's recent chat history:
{all_msgs}

Respond in valid JSON format ONLY:
{{
  "mood": "...",
  "motivation": "...",
  "predictive_preferences": ["..."],
  "manipulation_hooks": ["..."],
  "confidence_score": 85
}}
"""
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "status": "success",
                "profile": data,
                "confidence": data.get("confidence_score", 50)
            }
        else:
            return {"status": "error", "error": "Failed to parse JSON from LLM"}
    except Exception as e:
        logger.error(f"Psychology agent failed: {e}")
        return {"status": "error", "error": str(e)}
