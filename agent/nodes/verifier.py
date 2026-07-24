"""Strict verifier. Catches hallucinations before they reach the user."""
import json
from agent.state import AgentState, VerificationResult
from agent.llm.client import get_cheap_llm


PROMPT_TEMPLATE = """You are a strict verifier of outbound sales emails.
Your job is to catch hallucinations and ungrounded claims.

GROUND TRUTH (company research):
{research}

EMAIL DRAFT TO VERIFY:
Subject: {subject}
Body: {body}
Claimed personalization hooks: {hooks}

VERIFICATION CHECKS:
1. HALLUCINATIONS: Does the email state any fact NOT supported by the ground truth?
2. GROUNDING: Are the personalization hooks actually present in the ground truth?
3. QUALITY: Is the tone professional, specific, and non generic?

Be strict. A single hallucination should fail the check.

Return ONLY valid JSON with this exact schema, no other text:
{{
  "passed": true or false,
  "confidence": a number between 0.0 and 1.0,
  "issues": ["specific problems, empty list if none"],
  "grounded_claims": ["claims that ARE supported by the ground truth"]
}}
"""


# def verifier_node(state: AgentState) -> AgentState:
#     research_text = state.research.homepage_text[:3000] if state.research.homepage_text else ""
#     if state.research.search_results:
#         research_text += "\n\nSearch context:\n" + "\n".join(state.research.search_results[:3])

#     prompt = PROMPT_TEMPLATE.format(
#         research=research_text or "[no research data]",
#     if state.email_draft is None:
#         return {
#             "verification_passed": False,
#             "verification_notes": "Email draft was not generated"
#         }
#     subject=state.email_draft.subject,
#     body=state.email_draft.body,
#     hooks=", ".join(state.email_draft.personalization_hooks) or "none",
#     )

#     llm = get_cheap_llm(temperature=0.0)
#     try:
#         response = llm.invoke(prompt)
#         parsed = _extract_json(response.content)
#         result = VerificationResult(**parsed)
#     except Exception as e:
#         # If verifier itself fails, treat as unverified but do not crash the run
#         result = VerificationResult(
#             passed=False,
#             confidence=0.0,
#             issues=[f"verifier_parse_error: {e}"],
#             grounded_claims=[],
#         )
#         state.log(f"verify: PARSE ERROR, {e}")

#     state.verification = result
#     state.log(
#         f"verify: passed={result.passed} conf={result.confidence:.2f} "
#         f"issues={len(result.issues)} retry={state.retry_count}"
#     )
#     return state

def verifier_node(state: AgentState) -> AgentState:
    # Guard: if email draft failed, skip verification
    if state.email_draft is None:
        state.log("verify: SKIPPED, email_draft is None (drafter failed)")
        state.verification = VerificationResult(
            passed=False,
            confidence=0.0,
            issues=["email_draft was never generated"],
            grounded_claims=[],
        )
        return state

    research_text = state.research.homepage_text[:3000] if state.research.homepage_text else ""
    if state.research.search_results:
        research_text += "\n\nSearch context:\n" + "\n".join(state.research.search_results[:3])

    prompt = PROMPT_TEMPLATE.format(
        research=research_text or "[no research data]",
        subject=state.email_draft.subject,
        body=state.email_draft.body,
        hooks=", ".join(state.email_draft.personalization_hooks) or "none",
    )

    llm = get_cheap_llm(temperature=0.0)
    try:
        response = llm.invoke(prompt)
        parsed = _extract_json(response.content)
        result = VerificationResult(**parsed)
    except Exception as e:
        result = VerificationResult(
            passed=False,
            confidence=0.0,
            issues=[f"verifier_parse_error: {e}"],
            grounded_claims=[],
        )
        state.log(f"verify: PARSE ERROR, {e}")

    state.verification = result
    state.log(
        f"verify: passed={result.passed} conf={result.confidence:.2f} "
        f"issues={len(result.issues)} retry={state.retry_count}"
    )
    return state

def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object found: {text[:200]}")
    return json.loads(text[start:end])