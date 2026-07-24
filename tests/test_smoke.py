"""Smoke tests. Verify graph builds and state schema is sound."""
import pytest
from agent.state import AgentState, ICPDecision, EmailDraft, VerificationResult
from agent.graph import build_graph


def test_agent_state_defaults():
    state = AgentState(company_domain="example.com", icp_criteria="test criteria")
    assert state.status == "running"
    assert state.retry_count == 0
    assert state.trace == []


def test_icp_decision_confidence_bounds():
    with pytest.raises(Exception):
        ICPDecision(is_fit=True, confidence=1.5, reasoning="test")

    with pytest.raises(Exception):
        ICPDecision(is_fit=True, confidence=-0.1, reasoning="test")


def test_graph_builds():
    graph = build_graph()
    assert graph is not None


def test_state_serialization():
    state = AgentState(company_domain="test.com", icp_criteria="test")
    state.log("test entry")
    dumped = state.model_dump(mode="json")
    assert dumped["company_domain"] == "test.com"
    assert "test entry" in dumped["trace"]