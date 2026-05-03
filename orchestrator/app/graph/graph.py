from langgraph.graph import StateGraph, END
from .state import TripState
from .nodes import smart_chat, dispatch_agents, build_plan

def should_dispatch(state: TripState) -> str:
    """Only dispatch agents when we have enough info (stage >= 8)."""
    return "dispatch" if state.get("current_stage", 1) >= 8 else "end"

def build_trip_graph():
    g = StateGraph(TripState)
    g.add_node("chat",     smart_chat)
    g.add_node("dispatch", dispatch_agents)
    g.add_node("plan",     build_plan)

    g.set_entry_point("chat")
    g.add_conditional_edges("chat", should_dispatch, {
        "end": END,
        "dispatch": "dispatch"
    })
    g.add_edge("dispatch", "plan")
    g.add_edge("plan", END)
    return g.compile()

trip_graph = build_trip_graph()
