from langgraph.graph import StateGraph, END
from .state import TripState
from .nodes import stage_router, extract_stage_info, dispatch_agents, build_plan

def should_collect_more(state: TripState) -> str:
    return "collect" if state["current_stage"] <= 7 else "dispatch"

def build_trip_graph():
    g = StateGraph(TripState)
    g.add_node("route",    stage_router)
    g.add_node("extract",  extract_stage_info)
    g.add_node("dispatch", dispatch_agents)
    g.add_node("plan",     build_plan)

    g.set_entry_point("route")
    g.add_edge("route", "extract")
    g.add_conditional_edges("extract", should_collect_more, {
        "collect": "route",
        "dispatch": "dispatch"
    })
    g.add_edge("dispatch", "plan")
    g.add_edge("plan", END)
    return g.compile()

trip_graph = build_trip_graph()
