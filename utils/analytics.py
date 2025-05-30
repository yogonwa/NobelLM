import os
import requests

_plausible_domain = None
_plausible_api_url = "https://plausible.io/api/event"
_plausible_api_key = os.getenv("PLAUSIBLE_API_KEY")


def init_plausible(domain: str = None):
    """
    Initialize Plausible analytics tracking with the given domain.
    If not provided, uses the PLAUSIBLE_DOMAIN environment variable.
    """
    global _plausible_domain
    _plausible_domain = domain or os.getenv("PLAUSIBLE_DOMAIN")


def track_pageview(page: str):
    """
    Track a pageview event for the given page (e.g., 'home', 'about').
    """
    if not _plausible_domain:
        return
    data = {
        "name": "pageview",
        "url": f"https://{_plausible_domain}/{page}",
        "domain": _plausible_domain,
        "props": {"page": page},
    }
    headers = {"Content-Type": "application/json"}
    if _plausible_api_key:
        headers["Authorization"] = f"Bearer {_plausible_api_key}"
    try:
        requests.post(_plausible_api_url, json=data, headers=headers, timeout=2)
    except Exception:
        pass


def track_event(event_name: str, props: dict = None):
    """
    Track a custom event with the given name and optional properties.
    Do NOT include full queries or PII in props.
    """
    if not _plausible_domain:
        return
    data = {
        "name": event_name,
        "url": f"https://{_plausible_domain}/",
        "domain": _plausible_domain,
        "props": props or {},
    }
    headers = {"Content-Type": "application/json"}
    if _plausible_api_key:
        headers["Authorization"] = f"Bearer {_plausible_api_key}"
    try:
        requests.post(_plausible_api_url, json=data, headers=headers, timeout=2)
    except Exception:
        pass 