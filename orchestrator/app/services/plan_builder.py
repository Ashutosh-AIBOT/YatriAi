import json
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)

async def generate(state: dict, ranked_results: dict) -> dict:
    prompt = f"""
    Based on the user preferences and ranked agent results, generate a complete travel itinerary in JSON format.
    
    User Preferences: {json.dumps(state.get('user_prefs', {}))}
    Ranked Results: {json.dumps(ranked_results)[:2000]}
    
    Format the output STRICTLY as valid JSON with the following structure:
    {{
        "summary": "Short trip summary",
        "total_cost": 5000,
        "days": [
            {{
                "day": 1,
                "activities": [
                    {{"time": "10:00 AM", "description": "Activity details", "type": "transport|hotel|food|place"}}
                ]
            }}
        ]
    }}
    Return ONLY JSON, nothing else.
    """
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        extracted = json.loads(re.search(r'\{.*\}', response.content, re.DOTALL).group())
        return extracted
    except Exception as e:
        return {"days": [], "total_cost": 0, "summary": f"Plan generation failed: {str(e)}"}
