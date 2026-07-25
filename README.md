# Agentic Outreach Engine

**Live Demo:** https://agentic-outreach-engine-n74otwnzchxzaqjpausc2w.streamlit.app/

# Brief About System

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

Here is the flow:

Stage 1: Intake
Receives a company website (like "stripe.com") and validates it.

Stage 2: Research
Automatically scrapes the company's homepage and searches the web for recent news.

Stage 3: ICP Check (First Decision Point)
Decides if the company fits your ideal customer profile:

If NO → Stop here. Log it as "not a fit" and end.
If YES → Continue to write an email.
Stage 4: Draft
Writes a personalized cold email using AI, citing specific facts from the research.

Stage 5: Verify (Second Decision Point)
A separate AI checks if the email contains any made-up facts (hallucinations):

If PASSED → Go to final output.
If FAILED → Check retry budget:
If retries left → Send back to Draft with specific corrections (loop back)
If max retries hit → Output the draft anyway, but mark it "unverified"
Stage 6: Sink
Saves the final result (email + full audit trail) to a file.

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
