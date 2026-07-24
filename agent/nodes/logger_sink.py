"""Persist full agent state as JSON. Terminal node."""
import json
import os
import re
from datetime import datetime, timezone
from agent.state import AgentState


def logger_sink_node(state: AgentState) -> AgentState:
    os.makedirs("logs", exist_ok=True)

    safe_domain = re.sub(r"[^a-zA-Z0-9_.-]", "_", state.company_domain)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{safe_domain}_{timestamp}.json"

    payload = state.model_dump(mode="json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    if state.status not in ("not_fit", "failed"):
        state.status = "completed"

    state.log(f"sink: wrote {filename} status={state.status}")
    return state