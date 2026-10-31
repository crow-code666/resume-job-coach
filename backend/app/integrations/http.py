"""Small bounded JSON HTTP client for the app's fixed provider endpoints."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(Exception):
    def __init__(self, provider: str, status: int | None = None):
        self.provider = provider
        self.status = status
        super().__init__(f"{provider} request failed")


def get_json(url: str, provider: str, timeout: int = 12) -> dict:
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "CareerLensJobSearch/0.1"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ProviderError(provider)
        result = json.loads(raw)
    except HTTPError as error:
        raise ProviderError(provider, error.code) from None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        raise ProviderError(provider) from None
    if not isinstance(result, dict):
        raise ProviderError(provider)
    return result


def post_json(url: str, headers: dict[str, str], payload: dict, provider: str, timeout: int = 25) -> dict:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read(2_000_001))
    except HTTPError as error:
        raise ProviderError(provider, error.code) from None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        raise ProviderError(provider) from None
    if not isinstance(result, dict):
        raise ProviderError(provider)
    return result
