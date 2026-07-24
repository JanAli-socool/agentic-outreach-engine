"""Generate personalized outreach email. Strong model, grounded in research."""
import json, re
from agent.state import AgentState, EmailDraft
from agent.llm.client import get_strong_llm


PROMPT_TEMPLATE = """You write concise, high signal B2B outbound emails.

COMPANY RESEARCH (your only source of truth):
{homepage}

Additional context from search:
{snippets}

WHY THIS COMPANY MATCHES OUR ICP:
{reasoning}
Matched criteria: {matched}

STRICT RULES:
1. Subject line: max 8 words, specific to the company, no clickbait
2. Body: max 90 words, exactly 2 short paragraphs
3. Reference at least ONE specific detail from the research above. Do NOT invent facts.
4. End with a soft question, not a meeting request
5. No emojis, no "I hope this finds you well", no filler

{retry_context}

Return ONLY valid JSON with this exact schema, no other text:
{{
  "subject": "the subject line",
  "body": "the email body",
  "personalization_hooks": ["specific detail 1 from research", "specific detail 2 from research"]
}}
"""
def email_drafter_node(state: AgentState) -> AgentState:
    research = state.research
    homepage = research.homepage_text[:2500] if research.homepage_text else "[no homepage data]"
    snippets = "\n\n".join(research.search_results[:3]) if research.search_results else "[no search data]"

    retry_context = ""
    if state.verification and not state.verification.passed:
        retry_context = (
            "PREVIOUS ATTEMPT FAILED VERIFICATION. Issues found:\n"
            + "\n".join(f"- {issue}" for issue in state.verification.issues)
            + "\n\nFix these issues in this attempt."
        )

    prompt = PROMPT_TEMPLATE.format(
        homepage=homepage,
        snippets=snippets,
        reasoning=state.icp_decision.reasoning,
        matched=", ".join(state.icp_decision.matched_criteria) or "general fit",
        retry_context=retry_context,
    )

    llm = get_strong_llm(temperature=0.4)
    try:
            response = llm.invoke(prompt)
            parsed = _extract_json(response.content)
            draft = EmailDraft(**parsed)
    except Exception as e:
            state.status = "failed"
            state.error = f"Email drafter failed to parse LLM output: {e}"
            state.log(f"draft: FAILED, {e}")
            return state

    state.email_draft = draft
    state.retry_count += 1  # ← ADD THIS LINE
    state.log(f"draft: subject='{draft.subject}' hooks={len(draft.personalization_hooks)}")
    return state

# def _extract_json(text: str) -> dict:
#     import re
#     text = text.strip()
#     if text.startswith("```"):
#         text = text.split("```")[1]
#         if text.startswith("json"):
#             text = text[4:]
#     start = text.find("{")
#     end = text.rfind("}") + 1
#     if start == -1 or end <= start:
#         raise ValueError(f"No JSON object found: {text[:200]}")
    
#     json_str = text[start:end]
    
#     # Fix literal newlines inside JSON string values
#     # This replaces unescaped newlines/tabs inside strings
#     json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
#     json_str = re.sub(r'(?<!\\)\r', '\\r', json_str)
#     json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
    
#     return json.loads(json_str)

def _extract_json(text: str) -> dict:
    import re
    text = text.strip()
    
    # Strip markdown code fences
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.startswith("json"):
                text = part[4:].strip()
                break
            elif "{" in part:
                text = part.strip()
                break
    
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object found: {text[:200]}")
    
    json_str = text[start:end]
    
    # Use json5-style parsing: handle control characters properly
    # Strategy: parse character by character to fix unescaped newlines in string values
    fixed = _fix_json_string(json_str)
    return json.loads(fixed)


def _fix_json_string(s: str) -> str:
    """Fix unescaped control characters inside JSON string values."""
    result = []
    in_string = False
    escape_next = False
    
    for char in s:
        if escape_next:
            result.append(char)
            escape_next = False
            continue
        
        if char == '\\' and in_string:
            result.append(char)
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
            result.append(char)
            continue
        
        if in_string:
            # Replace control characters with their escaped versions
            if char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            else:
                result.append(char)
        else:
            result.append(char)
    
    return ''.join(result)



# def _extract_json(text: str) -> dict:
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