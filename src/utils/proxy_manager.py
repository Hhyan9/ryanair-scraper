from __future__ import annotations

from typing import Dict, Optional
from urllib.parse import urlparse

def build_proxies(proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Convert a single proxy URL into the `requests` proxies dict.
    Example:
        http://user:pass@host:port -> {"http": "...", "https": "..."}
    """
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid proxy URL scheme '{parsed.scheme}', expected http or https.")

    return {
        "http": proxy_url,
        "https": proxy_url,
    }