"""Tavily search. Structured, fast, agentic friendly."""
from tavily import TavilyClient
from agent.config import settings


def search_company(query: str, max_results: int = 5) -> tuple[list[str], bool]:
    """Return (snippets, failed_flag). Never raises."""
    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )
        snippets = []
        for result in response.get("results", []):
            title = result.get("title", "")
            content = result.get("content", "")
            snippets.append(f"{title}: {content}")
        return snippets, False
    except Exception:
        return [], True