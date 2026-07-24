"""Parallel tool execution: scrape + search."""
from concurrent.futures import ThreadPoolExecutor
from agent.state import AgentState, CompanyResearch
from agent.tools.scraper import scrape_homepage
from agent.tools.search import search_company


def research_node(state: AgentState) -> AgentState:
    domain = state.company_domain

    with ThreadPoolExecutor(max_workers=2) as executor:
        scrape_future = executor.submit(scrape_homepage, domain)
        search_future = executor.submit(
            search_company, f"{domain} company product overview"
        )

        homepage_text, scrape_failed = scrape_future.result()
        search_results, search_failed = search_future.result()

    state.research = CompanyResearch(
        domain=domain,
        homepage_text=homepage_text,
        search_results=search_results,
        scrape_failed=scrape_failed,
        search_failed=search_failed,
    )

    state.log(
        f"research: scrape_ok={not scrape_failed} "
        f"search_ok={not search_failed} "
        f"snippets={len(search_results)}"
    )

    # Hard fail if BOTH sources failed. Nothing to reason on.
    if scrape_failed and search_failed:
        state.status = "failed"
        state.error = "Both scrape and search failed. No research data."
        state.log("research: FAILED, no data available")

    return state