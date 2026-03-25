import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from models.schemas import AgentState, EngagementMode

from agents.cpt_landscape import cpt_landscape_node
from agents.policy_coverage import policy_coverage_node
from agents.gap_classifier import gap_classifier_node
from agents.narrative_generator import narrative_generator_node
from agents.ingestion import ingestion_node
from agents.payer_benchmark import payer_benchmark_node


def route_by_mode(state: AgentState) -> str:
    return state.request.engagement_mode.value


def route_after_gap(state: AgentState) -> str:
    if state.requires_human_review:
        return "human_review"
    return "narrative_generator"


def human_review_node(state: AgentState) -> AgentState:
    # HITL interrupt — LangGraph pauses here; analyst reviews via API
    return state


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Shared terminal nodes
    graph.add_node("gap_classifier", gap_classifier_node)
    graph.add_node("narrative_generator", narrative_generator_node)
    graph.add_node("human_review", human_review_node)

    # Feasibility path
    graph.add_node("cpt_landscape", cpt_landscape_node)
    graph.add_node("policy_coverage", policy_coverage_node)

    # Performance path
    graph.add_node("ingestion", ingestion_node)
    graph.add_node("payer_benchmark", payer_benchmark_node)

    # Entry routing
    graph.set_entry_point("cpt_landscape")  # overridden by conditional below
    graph.set_conditional_entry_point(
        route_by_mode,
        {
            EngagementMode.FEASIBILITY.value: "cpt_landscape",
            EngagementMode.PERFORMANCE.value: "ingestion",
        },
    )

    # Feasibility flow
    graph.add_edge("cpt_landscape", "policy_coverage")
    graph.add_edge("policy_coverage", "gap_classifier")

    # Performance flow
    graph.add_edge("ingestion", "payer_benchmark")
    graph.add_edge("payer_benchmark", "gap_classifier")

    # Shared terminal flow
    graph.add_conditional_edges("gap_classifier", route_after_gap, {
        "human_review": "human_review",
        "narrative_generator": "narrative_generator",
    })
    graph.add_edge("human_review", "narrative_generator")
    graph.add_edge("narrative_generator", END)

    checkpointer = PostgresSaver.from_conn_string(os.getenv("DATABASE_URL"))
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],
    )
