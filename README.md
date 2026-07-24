# Agentic Outreach Engine

🔗 **Live Demo:** https://agentic-outreach-engine-n74otwnzchxzaqjpausc2w.streamlit.app/
# agentic-outreach-engine

A production shaped agentic system that autonomously researches a company,
qualifies it against an Ideal Customer Profile (ICP), drafts a personalized
outbound email, verifies the output against source research to catch
hallucinations, and self corrects when verification confidence is low.

Built as a working demonstration of how I design agentic loops end to end:
stateful graph, conditional edges, tool use, verification, evals, and
production deployment.

---

## Architecture

The system is a LangGraph with 6 nodes and 4 conditional edges.

intake â†’ research â†’ icp â”€â”€[not_fit]â”€â”€â†’ sink
â”‚
â””â”€â”€[fit]â”€â”€â†’ draft â†’ verify â”€â”€[passed]â”€â”€â†’ sink
â”‚
â””â”€â”€[failed, retries left]â”€â”€â†’ draft (loop)
â”‚
â””â”€â”€[max retries hit]â”€â”€â†’ sink


### Nodes

| Node | Responsibility | Model |
|---|---|---|
| `intake` | Validate inputs, normalize domain | none |
| `research` | Parallel scrape + Tavily search | none |
| `icp` | Classify company vs ICP with reasoning | cheap (llama-3.1-8b) |
| `draft` | Generate personalized email, grounded in research | strong (llama-3.3-70b) |
| `verify` | Hallucination check, grounding check, tone check | cheap (llama-3.1-8b) |
| `sink` | Persist full state as JSON to disk | none |

### Key design decisions

- **State is typed** (Pydantic v2), not a dict. Every node signature is explicit.
- **Model routing:** cheap 8B model for classification and verification, strong 70B model only for final generation. This is a lesson from running LLM systems in production: cost is solved by routing, not by picking one model.
- **Self correction loop:** the verifier can force the drafter to retry with explicit feedback about what failed. Capped at 2 retries to prevent infinite loops.
- **Structured failure:** every tool returns `(data, failed_flag)` rather than raising. The graph handles missing data gracefully.
- **Trace is first class:** every node appends to `state.trace`. Debugging happens by reading the log, not by attaching a debugger.
- **Evals are first class:** `run_evals.py` measures ICP classification accuracy against a labeled dataset. An agentic system without evals is a demo, not a product.

---

## Running For Local & Docker Based

```bash
# Clone & setup
git clone https://github.com/JanAli-socool/agentic-outreach-engine.git
cd agentic-outreach-engine
cp .env.example .env   # Add Groq & Tavily keys

# Run locally
python -m scripts.run_single vercel.com

# Run eval suite
python -m scripts.run_evals

# Run with Docker
docker compose up --build
```

