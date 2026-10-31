"""Public regional job-board feeds plus direct live-search links."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
import re
from threading import Lock
from time import monotonic
from urllib.parse import urlencode, urlsplit

from app.career.role_profiles import get_role_profile
from app.integrations.http import ProviderError, get_json


ARBEITNOW_EU_URL = "https://www.arbeitnow.com/api/job-board-api?page=1"
ARBEITNOW_UK_URL = "https://www.arbeitnow.co.uk/api/job-board-api?page=1"
ARBEITNOW_CACHE_SECONDS = 20 * 60
STALE_CACHE_SECONDS = 2 * 24 * 60 * 60
MAX_RESULTS = 20

EUROPEAN_COUNTRIES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR",
    "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MT", "NL", "NO", "PL",
    "PT", "RO", "SE", "SI", "SK", "SM", "VA",
}
COUNTRY_ALIASES = {
    "IN": ("india", "indian"),
    "US": ("united states", "usa", "america", "\bus\b"),
    "GB": ("united kingdom", "uk", "britain", "england", "scotland", "wales"),
    "CA": ("canada",),
    "AU": ("australia",),
    "DE": ("germany",),
    "SG": ("singapore",),
    "FR": ("france",),
    "NL": ("netherlands", "holland"),
}
ROLE_STOP_WORDS = {"a", "an", "and", "entry", "full", "graduate", "intern", "internship", "job", "jobs", "junior", "level", "of", "role", "senior", "the"}

_cache: dict[str, tuple[float, float, dict]] = {}
_cache_lock = Lock()


def _cached_feed(url: str, name: str, ttl: int) -> dict:
    now = monotonic()
    with _cache_lock:
        cached = _cache.get(url)
        if cached and cached[0] > now:
            return cached[2]

    try:
        result = get_json(url, name)
    except ProviderError:
        with _cache_lock:
            stale = _cache.get(url)
            if stale and stale[1] > now:
                return stale[2]
        raise

    with _cache_lock:
        _cache[url] = (now + ttl, now + ttl + STALE_CACHE_SECONDS, result)
    return result


def _feed_specs(country_code: str) -> list[tuple[str, str, int]]:
    if country_code == "GB":
        return [("Arbeitnow UK", ARBEITNOW_UK_URL, ARBEITNOW_CACHE_SECONDS)]
    if country_code in EUROPEAN_COUNTRIES:
        return [("Arbeitnow Europe", ARBEITNOW_EU_URL, ARBEITNOW_CACHE_SECONDS)]
    if country_code == "GLOBAL":
        return [
            ("Arbeitnow Europe", ARBEITNOW_EU_URL, ARBEITNOW_CACHE_SECONDS),
            ("Arbeitnow UK", ARBEITNOW_UK_URL, ARBEITNOW_CACHE_SECONDS),
        ]
    return []


def _text(value: object, limit: int = 4000) -> str:
    if isinstance(value, (list, tuple, set)):
        value = ", ".join(str(item) for item in value)
    if value is None:
        return ""
    value = unescape(re.sub(r"<[^>]*>", " ", str(value)))
    return " ".join(value.split())[:limit]


def _tags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in value:
        item = _text(raw, 60)
        key = item.casefold()
        if item and key not in seen:
            result.append(item)
            seen.add(key)
        if len(result) == 8:
            break
    return result


def _date(value: object) -> str:
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()
        return _text(value, 40)[:10]
    except (OverflowError, OSError, ValueError):
        return ""


def _normalize_listing(item: dict, provider: str) -> dict | None:
    title = _text(item.get("title"), 240)
    url = _text(item.get("url"), 2048)
    try:
        parsed_url = urlsplit(url)
    except ValueError:
        return None
    host = (parsed_url.hostname or "").casefold()
    if not title or parsed_url.scheme != "https":
        return None
    if host not in {"arbeitnow.com", "www.arbeitnow.com", "arbeitnow.co.uk", "www.arbeitnow.co.uk"}:
        return None

    tags = _tags(item.get("tags"))
    location = _text(item.get("location"), 160)
    types = item.get("job_types")
    job_type = _text(types[0], 60).replace("_", " ").title() if isinstance(types, list) and types else ""
    remote = bool(item.get("remote"))
    publication_date = _date(item.get("created_at"))
    salary = ""
    company = _text(item.get("company_name"), 180)

    description = _text(item.get("description"), 4000)
    if not location and remote:
        location = "Remote; eligibility not specified"
    return {
        "title": title,
        "url": url,
        "snippet": description[:520] or "Open the source listing for the full job details.",
        "published_date": publication_date,
        "source": provider,
        "company": company,
        "location": location,
        "job_type": job_type,
        "remote": remote,
        "salary": salary,
        "tags": tags,
    }


def _role_tokens(role: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9+#.]+", role.casefold())
        if len(token) > 1 and token not in ROLE_STOP_WORDS
    ]


def _role_score(role: str, listing: dict) -> float:
    tokens = _role_tokens(role)
    if not tokens:
        return 0
    title = " ".join(re.findall(r"[a-z0-9+#.]+", listing["title"].casefold()))
    tags = " ".join(re.findall(r"[a-z0-9+#.]+", " ".join(listing["tags"]).casefold()))
    body = " ".join(re.findall(r"[a-z0-9+#.]+", listing["snippet"].casefold()))
    phrase = " ".join(tokens)
    score = 10 if phrase in title else 0
    title_matches = sum(token in title.split() for token in tokens)
    tag_matches = sum(token in tags.split() for token in tokens)
    body_matches = sum(token in body.split() for token in tokens)
    score += 4 * title_matches + 2 * tag_matches + min(body_matches, 3) * 0.4
    if title_matches == 0 and tag_matches == 0 and body_matches < min(2, len(tokens)):
        return 0
    return score


def _location_matches(listing: dict, country_code: str, country_name: str, city: str) -> bool:
    if country_code == "GLOBAL":
        return True
    location = listing["location"].casefold().strip()
    if not location or location in {"remote", "remote; eligibility not specified", "multiple locations"}:
        return True
    normalized = " ".join(re.findall(r"[a-z0-9]+", location))
    targets = [country_name, city, *COUNTRY_ALIASES.get(country_code, ())]
    for target in targets:
        target = target.strip().casefold()
        if not target:
            continue
        if target.startswith("\\b") and re.search(target, location):
            return True
        if target in normalized:
            return True
    if any(term in normalized for term in ("worldwide", "anywhere", "global", "all countries", "all locations")):
        return True
    if country_code in EUROPEAN_COUNTRIES | {"GB"} and "europe" in normalized:
        return True
    return False


def _fetch_feeds(specs: list[tuple[str, str, int]]) -> tuple[list[dict], list[str]]:
    listings: list[dict] = []
    available: list[str] = []
    errors = 0
    if not specs:
        return listings, available
    with ThreadPoolExecutor(max_workers=max(1, len(specs))) as executor:
        futures = {executor.submit(_cached_feed, url, name, ttl): name for name, url, ttl in specs}
        for future in as_completed(futures):
            name = futures[future]
            try:
                payload = future.result()
            except ProviderError:
                errors += 1
                continue
            raw_items = payload.get("data")
            if not isinstance(raw_items, list):
                errors += 1
                continue
            available.append(name)
            for raw in raw_items:
                if isinstance(raw, dict):
                    listing = _normalize_listing(raw, name)
                    if listing:
                        listings.append(listing)
    if not available and errors:
        raise ProviderError("Public job sources")
    return listings, available


def _location_label(country_code: str, country_name: str, city: str) -> str:
    if country_code == "GLOBAL":
        return "global / remote"
    return f"{city.strip()}, {country_name.strip()}" if city.strip() else country_name.strip()


def _external_search_links(role: str, country_code: str, country_name: str, city: str) -> list[dict[str, str]]:
    location = _location_label(country_code, country_name, city)
    query = f"{role} jobs {location}"
    indeed_hosts = {
        "IN": "in.indeed.com", "US": "www.indeed.com", "GB": "uk.indeed.com", "CA": "ca.indeed.com",
        "AU": "au.indeed.com", "DE": "de.indeed.com", "SG": "sg.indeed.com", "FR": "fr.indeed.com",
        "NL": "nl.indeed.com",
    }
    indeed_host = indeed_hosts.get(country_code, "www.indeed.com")
    links = [
        {
            "label": "Google Search",
            "url": f"https://www.google.com/search?{urlencode({'q': query})}",
            "description": "Search the web for this role and location.",
            "category": "jobs",
        },
        {
            "label": "Indeed",
            "url": f"https://{indeed_host}/jobs?{urlencode({'q': role, 'l': location})}",
            "description": f"Open Indeed results for {location}.",
            "category": "jobs",
        },
        {
            "label": "LinkedIn Jobs",
            "url": f"https://www.linkedin.com/jobs/search/?{urlencode({'keywords': role, 'location': location})}",
            "description": f"Open LinkedIn job results for {location}.",
            "category": "jobs",
        },
        {
            "label": "GitHub projects",
            "url": f"https://github.com/search?{urlencode({'q': f'{role} project', 'type': 'repositories'})}",
            "description": "Explore related repositories and portfolio examples; this is not a job board.",
            "category": "projects",
        },
    ]
    profile, specialized = get_role_profile(role)
    roadmap_path = profile.roadmap_slug if specialized and profile.roadmap_slug else "roadmaps"
    links.append({
        "label": "roadmap.sh learning path",
        "url": f"https://roadmap.sh/{roadmap_path}",
        "description": "Open a role-related learning roadmap; this is not a job board.",
        "category": "learning",
    })
    if country_code == "IN":
        links.append({
            "label": "Naukri via Google",
            "url": f"https://www.google.com/search?{urlencode({'q': f'site:naukri.com {role} jobs {location}'})}",
            "description": "Search Naukri listings through Google.",
            "category": "jobs",
        })
    return links


def search_public_jobs(role: str, country_code: str, country_name: str, city: str = "") -> dict:
    specs = _feed_specs(country_code)
    try:
        all_listings, providers = _fetch_feeds(specs)
        feed_error = False
    except ProviderError:
        all_listings, providers = [], []
        feed_error = True
    results = [
        listing for listing in all_listings
        if _role_score(role, listing) > 0 and _location_matches(listing, country_code, country_name, city)
    ]
    results.sort(key=lambda item: (_role_score(role, item), item["published_date"]), reverse=True)

    seen: set[str] = set()
    unique: list[dict] = []
    for result in results:
        key = result["url"].casefold()
        if key not in seen:
            unique.append(result)
            seen.add(key)
        if len(unique) == MAX_RESULTS:
            break

    location = _location_label(country_code, country_name, city)
    provider_text = ", ".join(providers) or "public job feeds"
    if feed_error:
        summary = (
            "The connected job feeds could not be reached just now. Use the live job-board searches below; "
            "they open directly on the selected providers."
        )
    elif unique:
        summary = (
            f"Found {len(unique)} relevant listings for {role} in {location} from {provider_text}. "
            "This is a sample of the connected public feeds, not the whole job market. Check each source for current status and work-location eligibility."
        )
    elif not providers:
        summary = (
            f"There is no connected in-app job feed for {location} yet. Use the live searches below to open current results on major job sites."
        )
    else:
        summary = (
            f"No matching listings appeared in the connected public feeds for {role} in {location}. "
            "Try a broader role title or choose Global / other to include more remote listings."
        )
    return {"query": role, "summary": summary, "results": unique, "search_links": _external_search_links(role, country_code, country_name, city)}


def public_market_pulse(role: str, country_code: str, country_name: str, city: str = "") -> dict:
    report = search_public_jobs(role, country_code, country_name, city)
    location = _location_label(country_code, country_name, city)
    report["search_links"].append({
        "label": "Hiring trends",
        "url": f"https://www.google.com/search?{urlencode({'q': f'{role} hiring trends in {location}'})}",
        "description": f"Search current hiring trends for {role} in {location}.",
        "category": "market",
    })
    tag_counts: Counter[str] = Counter()
    for item in report["results"]:
        tag_counts.update(tag.strip() for tag in item.get("tags", []) if tag.strip())
    frequent = [tag for tag, _count in tag_counts.most_common(5)]
    if report["results"] and frequent:
        report["summary"] = (
            f"In this sample of {len(report['results'])} public listings for {role} in {location}, "
            f"frequent listing tags include {', '.join(frequent)}. This is a signal from connected job feeds, "
            "not a complete labor-market survey or salary estimate. Open the sources to verify details."
        )
    elif report["results"]:
        report["summary"] = (
            f"The connected public feeds returned {len(report['results'])} listings for {role} in {location}. "
            "This is a limited sample, not a complete labor-market survey or salary estimate."
        )
    elif not report["results"] and not _feed_specs(country_code):
        report["summary"] = (
            f"No connected in-app job feed covers {location}, so CareerLens cannot calculate a local listing sample. "
            "Use the live job and hiring-trend searches below for current results."
        )
    elif not report["results"] and "could not be reached" in report["summary"].casefold():
        report["summary"] = (
            f"The public job feed was unavailable, so CareerLens could not calculate a listing sample for {role} in {location}. "
            "Use the live job and hiring-trend searches below for current results."
        )
    else:
        report["summary"] = (
            f"No matching listings were available for a market signal for {role} in {location}. "
            "Try a broader role title or Global / other."
        )
    return report
