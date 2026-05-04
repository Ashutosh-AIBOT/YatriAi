import asyncio
import json
from orchestrator.app.graph.state import TripState
from orchestrator.app.graph.nodes import smart_chat, dispatch_agents, build_plan
import uuid

async def main():
    state = {
        "trip_id": str(uuid.uuid4()),
        "user_id": "test_user",
        "chat_mode": "planning",
        "current_stage": 1,
        "messages": [
            {"role": "user", "content": "I am so tired of my boring job, I want an adventurous trip to the mountains. I need adrenaline!"}
        ],
        "origin": "Delhi",
        "destination": "Manali",
        "transport_modes": ["bus"],
        "total_budget": 50000,
        "group_size": 2,
        "user_prefs": {"notes": "Loves hiking, hates crowds"},
        "research_pass": 0,
        "agent_statuses": {}
    }
    
    print("Testing psychology agent dispatch...")
    state["current_stage"] = 8 # trigger dispatch
    new_state = await dispatch_agents(state)
    print("Psychology profile:", json.dumps(new_state.get("psychology_results"), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
