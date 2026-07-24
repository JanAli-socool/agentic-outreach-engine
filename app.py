"""
Streamlit UI for the Agentic Outreach Engine.

Design decisions worth noting:
- Live trace streaming: users see the graph executing node-by-node, not a black box
- Uncertainty is surfaced (confidence scores, verification status), not hidden
- Failures are shown explicitly with context, not swallowed
- Progressive disclosure: research is collapsed by default, email draft is prominent
- Retries are visually explained so users understand the self-correction loop
"""
import streamlit as st
import time
from agent.graph import build_graph
from agent.state import AgentState
from agent.config import settings


# ---------- Page config ----------
st.set_page_config(
    page_title="Agentic Outreach Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Sidebar: inputs and config ----------
with st.sidebar:
    st.title("🎯 Agentic Outreach")
    st.caption("LangGraph pipeline with grounded verification loop")

    st.divider()

    domain = st.text_input(
        "Company Domain",
        value="stripe.com",
        placeholder="e.g. vercel.com",
        help="The target company to research and reach out to",
    )

    icp_criteria = st.text_area(
        "ICP Criteria",
        value=(
            "B2B SaaS company; "
            "10-300 employees; "
            "focused on AI, developer tools, or data infrastructure; "
            "based in US, Canada, or Europe; "
            "shows signs of active product development and growth (hiring, recent launches, funding)"
        ),
        height=150,
        help="What makes a good-fit company for outreach",
    )

    st.divider()

    with st.expander("⚙️ Advanced settings"):
        st.text(f"Cheap model: {settings.cheap_model}")
        st.text(f"Strong model: {settings.strong_model}")
        st.text(f"Max verifier retries: {settings.max_verifier_retries}")
        st.text(f"Confidence threshold: {settings.confidence_threshold}")

    st.divider()

    run_button = st.button("▶ Run Pipeline", type="primary", use_container_width=True)


# ---------- Main area ----------
st.title("Agentic Outreach Engine")
st.markdown(
    "This system researches a company, classifies ICP fit, drafts a grounded outreach email, "
    "and self-corrects hallucinations via a verifier loop. Watch the pipeline execute live."
)

# Status placeholder for the live trace
trace_container = st.container()
results_container = st.container()


def status_badge(status: str) -> str:
    """Render a colored badge for pipeline status."""
    colors = {
        "completed": "🟢",
        "failed": "🔴",
        "not_fit": "🟡",
        "running": "🔵",
    }
    return f"{colors.get(status, '⚪')} {status.upper()}"


def confidence_bar(value: float, label: str = "Confidence") -> None:
    """Visual confidence indicator."""
    st.progress(value, text=f"{label}: {value:.0%}")


# ---------- Execute pipeline ----------
if run_button:
    if not domain.strip():
        st.error("Please enter a company domain")
        st.stop()

    with trace_container:
        st.subheader("Live Trace")
        trace_placeholder = st.empty()

    # Seed initial state
    initial_state = AgentState(
        company_domain=domain.strip(),
        icp_criteria=icp_criteria.strip(),
    )

    # Build the graph
    graph = build_graph()

    # Run the pipeline (LangGraph is synchronous — we render trace after each step)
    trace_lines = []
    trace_placeholder.info("🚀 Starting pipeline...")

    try:
        # Use stream to show progressive updates
        final_state = None
        for step in graph.stream(initial_state, {"recursion_limit": 50}):
            # step is a dict: {node_name: state_after_node}
            for node_name, state in step.items():
                # state comes back as dict from LangGraph, reconstruct trace
                if isinstance(state, dict) and "trace" in state:
                    current_trace = state["trace"]
                    if len(current_trace) > len(trace_lines):
                        trace_lines = current_trace
                        # Render live trace
                        trace_text = "\n".join(f"  • {line}" for line in trace_lines)
                        trace_placeholder.code(trace_text, language="text")
                final_state = state

        # Reconstruct AgentState from final dict for rendering
        if isinstance(final_state, dict):
            final_state = AgentState(**final_state)

    except Exception as e:
        st.error(f"Pipeline crashed: {e}")
        st.stop()

    # ---------- Render results ----------
    with results_container:
        st.divider()
        st.subheader("Results")

        # Top-level status
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### {status_badge(final_state.status)}")
        with col2:
            st.metric("Retries", final_state.retry_count)
        with col3:
            st.metric("Trace steps", len(final_state.trace))

        if final_state.error:
            st.error(f"⚠️ Error: {final_state.error}")

        # ---------- ICP Decision ----------
        if final_state.icp_decision:
            st.divider()
            st.subheader("🎯 ICP Classification")

            icp = final_state.icp_decision
            col_a, col_b = st.columns([1, 3])
            with col_a:
                if icp.is_fit:
                    st.success("✅ FIT")
                else:
                    st.warning("❌ NOT A FIT")
                confidence_bar(icp.confidence, "Confidence")

            with col_b:
                st.markdown("**Reasoning:**")
                st.info(icp.reasoning)

                if icp.matched_criteria:
                    st.markdown("**Matched criteria:**")
                    for c in icp.matched_criteria:
                        st.markdown(f"- ✅ {c}")

                if icp.missing_criteria:
                    st.markdown("**Missing criteria:**")
                    for c in icp.missing_criteria:
                        st.markdown(f"- ⚠️ {c}")

        # ---------- Email Draft ----------
        if final_state.email_draft:
            st.divider()
            st.subheader("✉️ Email Draft")

            draft = final_state.email_draft

            # Show verification status prominently above the email
            if final_state.verification:
                if final_state.verification.passed:
                    st.success(
                        f"✅ Verified (confidence {final_state.verification.confidence:.0%}) "
                        f"— every claim grounded in research"
                    )
                else:
                    st.warning(
                        f"⚠️ Unverified draft (confidence {final_state.verification.confidence:.0%}) "
                        f"— review before sending"
                    )

            # Email card
            with st.container(border=True):
                st.markdown(f"**Subject:** {draft.subject}")
                st.divider()
                st.markdown(draft.body)
                st.divider()
                st.markdown("**Personalization hooks used:**")
                for h in draft.personalization_hooks:
                    st.markdown(f"- 📌 {h}")

        # ---------- Verification Details ----------
        if final_state.verification:
            st.divider()
            st.subheader("🛡️ Verification Details")

            v = final_state.verification

            col_x, col_y = st.columns([1, 3])
            with col_x:
                if v.passed:
                    st.success("PASSED")
                else:
                    st.error("FAILED")
                confidence_bar(v.confidence, "Verifier confidence")

            with col_y:
                if v.issues:
                    st.markdown("**Issues found:**")
                    for issue in v.issues:
                        st.markdown(f"- 🔴 {issue}")

                if v.grounded_claims:
                    st.markdown("**Grounded claims (backed by research):**")
                    for claim in v.grounded_claims:
                        st.markdown(f"- ✅ {claim}")

        # ---------- Research (collapsed by default) ----------
        if final_state.research:
            with st.expander("🔍 View raw research data (ground truth)"):
                r = final_state.research
                col_p, col_q = st.columns(2)
                with col_p:
                    st.metric("Scrape", "✅ OK" if not r.scrape_failed else "❌ Failed")
                with col_q:
                    st.metric("Search", "✅ OK" if not r.search_failed else "❌ Failed")

                st.markdown("**Homepage extract:**")
                st.text(r.homepage_text[:2000] + ("..." if len(r.homepage_text) > 2000 else ""))

                if r.search_results:
                    st.markdown("**Search snippets:**")
                    for i, s in enumerate(r.search_results[:5], 1):
                        st.markdown(f"**{i}.** {s}")

        # ---------- Full trace (collapsed) ----------
        with st.expander("📜 Full execution trace"):
            st.code("\n".join(final_state.trace), language="text")


else:
    # Initial state — show explainer
    st.info(
        "👈 Enter a company domain in the sidebar and click **Run Pipeline** to start. "
        "Try `stripe.com` (passes verification), `vercel.com` (triggers retry loop), "
        "or `mcdonalds.com` (short-circuits as non-fit)."
    )

    with st.expander("How the pipeline works"):
        st.markdown("""
        The system runs a **6-node LangGraph pipeline**:

        1. **Intake** — Validates and normalizes the domain
        2. **Research** — Scrapes homepage + Tavily search in parallel
        3. **ICP Classifier** — Cheap LLM decides fit against your criteria
        4. **Drafter** — Strong LLM writes a grounded email
        5. **Verifier** — Cheap LLM checks every claim against research
        6. **Sink** — Logs full state to disk

        If the verifier catches hallucinations, the pipeline **loops back** to the drafter
        with specific feedback. Max 2 retries, then it ships whatever draft exists with
        verification status attached.
        """)