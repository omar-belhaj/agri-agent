r"""
Construction du graphe LangGraph représentant la boucle agentique :

    observer -> decider --(anomalie)--> research -> act
                        \--(pas d'anomalie)--------> act
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    observer_node,
    decider_node,
    research_node,
    act_node,
    route_after_decision,
)


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("observer", observer_node)
    graph.add_node("decider", decider_node)
    graph.add_node("research", research_node)
    graph.add_node("act", act_node)

    graph.set_entry_point("observer")
    graph.add_edge("observer", "decider")

    graph.add_conditional_edges(
        "decider",
        route_after_decision,
        {
            "research": "research",
            "act": "act",
        },
    )

    graph.add_edge("research", "act")
    graph.add_edge("act", END)

    return graph.compile()
