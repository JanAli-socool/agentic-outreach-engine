"""LLM classifies company vs ICP with structured output."""
import json
from agent.state import AgentState, ICPDecision
from agent.llm.client import get_cheap_llm


PROMPT_TEMPLATE = """You are an ICP (Ideal Customer Profile) classifier for B2B sales qualification.

ICP CRITERIA:
{icp_criteria}

COMPANY RESEARCH:

Homepage extract:
{homepage}

Search results:
{snippets}

TASK:
Decide if this company fits the ICP. Base your decision ONLY on the research above.
If the research is thin, lower your confidence accordingly.

Return ONLY valid JSON with this exact schema, no other text:
{{
  "is_fit": true or false,
  "confidence": a number between 0.0 and 1.0,
  "reasoning": "2 to 3 sentences explaining your decision",
  "matched_criteria": ["criteria the company clearly meets"],
  "missing_criteria": ["criteria not met or unclear"]
}}
"""


def icp_classifier_node(state: AgentState) -> AgentState:
    research = state.research
    homepage = research.homepage_text[:3000] if research.homepage_text else "[no homepage data]"
    snippets = "\n\n".join(research.search_results[:5]) if research.search_results else "[no search data]"

    prompt = PROMPT_TEMPLATE.format(
        icp_criteria=state.icp_criteria,
        homepage=homepage,
        snippets=snippets,
    )

    llm = get_cheap_llm(temperature=0.0)
    try:
        response = llm.invoke(prompt)
        parsed = _extract_json(response.content)
        decision = ICPDecision(**parsed)
    except Exception as e:
        state.status = "failed"
        state.error = f"ICP classifier failed to parse LLM output: {e}"
        state.log(f"icp: FAILED, {e}")
        return state

    state.icp_decision = decision

    if not decision.is_fit:
        state.status = "not_fit"

    state.log(
        f"icp: fit={decision.is_fit} conf={decision.confidence:.2f} "
        f"matched={len(decision.matched_criteria)} missing={len(decision.missing_criteria)}"
    )
    return state


def _extract_json(text: str) -> dict:
    """Robust JSON extraction. Handles LLMs that wrap JSON in prose or code fences."""
    text = text.strip()
    if text.startswith("```"):
        # strip code fence
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object found in LLM output: {text[:200]}")
    return json.loads(text[start:end])