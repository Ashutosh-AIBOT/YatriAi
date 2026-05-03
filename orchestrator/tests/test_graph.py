import pytest
from app.graph.state import TripState
from app.graph.graph import trip_graph

@pytest.mark.asyncio
async def test_graph_router_to_extract():
    # Initial state
    state = TripState(
        trip_id="123",
        user_id="user_1",
        user_prefs={},
        current_stage=1,
        messages=[]
    )
    
    # Run the graph for one node
    # It should go from entry -> route -> extract, then pause or continue
    result = await trip_graph.ainvoke(state)
    
    assert result["current_stage"] == 2
    assert len(result["messages"]) > 0
    assert result["messages"][0]["role"] == "assistant"
