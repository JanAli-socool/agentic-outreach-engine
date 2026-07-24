"""Validate and initialize agent state."""
from agent.state import AgentState


def intake_node(state: AgentState) -> AgentState:
    if not state.company_domain or not state.company_domain.strip():
        state.status = "failed"
        state.error = "company_domain is required"
        state.log("intake: FAILED, missing domain")
        return state

    if not state.icp_criteria or not state.icp_criteria.strip():
        state.status = "failed"
        state.error = "icp_criteria is required"
        state.log("intake: FAILED, missing ICP criteria")
        return state

    state.company_domain = state.company_domain.strip().lower()
    state.log(f"intake: accepted domain={state.company_domain}")
    return state