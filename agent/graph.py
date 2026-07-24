"""LangGraph definition. This is the heart of the system."""
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.config import settings
from agent.nodes.intake import intake_node
from agent.nodes.research import research_node
from agent.nodes.icp_classifier import icp_classifier_node
from agent.nodes.email_drafter import email_drafter_node
from agent.nodes.verifier import verifier_node
from agent.nodes.logger_sink import logger_sink_node


# Node keys are deliberately prefixed to avoid collision with AgentState fields
# (LangGraph requires node names to not overlap with state channel names).
NODE_INTAKE = "n_intake"
NODE_RESEARCH = "n_research"
NODE_ICP = "n_icp"
NODE_DRAFT = "n_draft"
NODE_VERIFY = "n_verify"
NODE_SINK = "n_sink"


def route_after_intake(state: AgentState) -> str:
    if state.status == "failed":
        return NODE_SINK
    return NODE_RESEARCH


def route_after_research(state: AgentState) -> str:
    if state.status == "failed":
        return NODE_SINK
    return NODE_ICP


def route_after_icp(state: AgentState) -> str:
    if state.status in ("failed", "not_fit"):
        return NODE_SINK
    return NODE_DRAFT


def route_after_verify(state: AgentState) -> str:
    """Self correction loop: retry drafter on low confidence, up to max retries."""
    if state.status == "failed":
        return NODE_SINK

    verification = state.verification
    if verification is None:
        return NODE_SINK

    if verification.passed and verification.confidence >= settings.confidence_threshold:
        return NODE_SINK

    if state.retry_count >= settings.max_verifier_retries:
        return NODE_SINK

    # Do NOT mutate state here - let the drafter node handle retry_count
    return NODE_DRAFT


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node(NODE_INTAKE, intake_node)
    graph.add_node(NODE_RESEARCH, research_node)
    graph.add_node(NODE_ICP, icp_classifier_node)
    graph.add_node(NODE_DRAFT, email_drafter_node)
    graph.add_node(NODE_VERIFY, verifier_node)
    graph.add_node(NODE_SINK, logger_sink_node)

    graph.set_entry_point(NODE_INTAKE)

    graph.add_conditional_edges(
        NODE_INTAKE,
        route_after_intake,
        {NODE_RESEARCH: NODE_RESEARCH, NODE_SINK: NODE_SINK},
    )
    graph.add_conditional_edges(
        NODE_RESEARCH,
        route_after_research,
        {NODE_ICP: NODE_ICP, NODE_SINK: NODE_SINK},
    )
    graph.add_conditional_edges(
        NODE_ICP,
        route_after_icp,
        {NODE_DRAFT: NODE_DRAFT, NODE_SINK: NODE_SINK},
    )
    # graph.add_edge(NODE_DRAFT, NODE_VERIFY)
    graph.add_conditional_edges(
    NODE_DRAFT,
    lambda state: NODE_SINK if state.status == "failed" else NODE_VERIFY,
    {NODE_VERIFY: NODE_VERIFY, NODE_SINK: NODE_SINK},
    )
    graph.add_conditional_edges(
        NODE_VERIFY,
        route_after_verify,
        {NODE_DRAFT: NODE_DRAFT, NODE_SINK: NODE_SINK},
    )
    graph.add_edge(NODE_SINK, END)

    return graph.compile()