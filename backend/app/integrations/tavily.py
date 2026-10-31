"""Tavily Search API adapter; never returns provider credentials to clients."""

from app.integrations.http import ProviderError, post_json


def search(api_key: str, query: str, country: str | None = None) -> dict:
    payload = {
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
        "topic": "general",
        "include_answer": True,
        "include_raw_content": False,
        "safe_search": True,
    }
    if country:
        payload["country"] = country
    return post_json(
        "https://api.tavily.com/search",
        {"Authorization": f"Bearer {api_key}"},
        payload,
        "Tavily",
        timeout=30,
    )
