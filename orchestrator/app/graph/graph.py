from langgraph.graph import StateGraph, END
from .state import TripState
from .nodes import smart_chat, dispatch_agents, build_plan, run_single_agent


def should_dispatch(state: TripState) -> str:
    """Route after chat:
    - If ready to plan (stage >= 8) → dispatch all agents
    - If a single agent is targeted → run_single
    - Otherwise → end (just chatting)
    """
    if state.get("target_agent") and state.get("current_stage", 1) < 8:
        return "run_single"
    if state.get("current_stage", 1) >= 8:
        return "dispatch"
    return "end"


def build_trip_graph():
    g = StateGraph(TripState)

    # Nodes
    g.add_node("chat",        smart_chat)
    g.add_node("dispatch",    dispatch_agents)
    g.add_node("plan",        build_plan)
    g.add_node("run_single",  run_single_agent)

    # Entry
    g.set_entry_point("chat")

    # Routing after chat
    g.add_conditional_edges("chat", should_dispatch, {
        "end": END,
        "dispatch": "dispatch",
        "run_single": "run_single",
    })

    # After dispatching all agents → build the plan
    g.add_edge("dispatch", "plan")
    g.add_edge("plan", END)

    # After single agent run → end
    g.add_edge("run_single", END)

    return g.compile()


trip_graph = build_trip_graph()
