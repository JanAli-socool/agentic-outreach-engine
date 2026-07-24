"""Web scraper. Returns structured failure instead of raising."""
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from agent.config import settings


class ScrapeError(Exception):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    reraise=True,
)
def _fetch(url: str, timeout: int) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


def scrape_homepage(domain: str) -> tuple[str, bool]:
    """Return (text, failed_flag). Never raises."""
    url = domain if domain.startswith("http") else f"https://{domain}"
    try:
        html = _fetch(url, settings.scrape_timeout_seconds)
    except Exception:
        return "", True

    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return text[: settings.scrape_max_chars], False
    except Exception:
        return "", True