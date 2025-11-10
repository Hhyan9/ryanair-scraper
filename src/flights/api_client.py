from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from .validator import FlightSearchQuery

class RyanairApiClient:
    """
    Simple HTTP client for Ryanair public availability endpoint.

    This client is intentionally minimal but robust enough for production-style usage:
    - timeouts
    - proxy support
    - basic retry loop (for transient network errors)
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        proxies: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.proxies = proxies
        self.logger = logger or logging.getLogger(__name__)
        self.max_retries = max_retries

    def _build_params(self, query: FlightSearchQuery) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "Origin": query.origin,
            "Destination": query.destination,
            "DateOut": query.date_from,
            "ADT": query.adults,
            "TEEN": query.teens,
            "CHD": query.children,
            "INF": query.infants,
            "ToUs": "AGREED",
            "IncludeConnectingFlights": "false",
            "FlexDaysBeforeOut": 0,
            "FlexDaysOut": 0,
            "RoundTrip": "true" if query.trip_type == "ROUND_TRIP" else "false",
            "Currency": query.currency,
        }
        if query.trip_type == "ROUND_TRIP" and query.date_to:
            params["DateIn"] = query.date_to
            params["FlexDaysBeforeIn"] = 0
            params["FlexDaysIn"] = 0

        return params

    def search_flights(self, query: FlightSearchQuery) -> Dict[str, Any]:
        params = self._build_params(query)
        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt <= self.max_retries:
            attempt += 1
            try:
                self.logger.debug("Requesting Ryanair availability, attempt %d", attempt)
                resp = requests.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                    proxies=self.proxies,
                )
                self.logger.debug("Ryanair API status code: %s", resp.status_code)
                resp.raise_for_status()
                return resp.json()
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                self.logger.warning(
                    "Network error while calling Ryanair API (attempt %d/%d): %s",
                    attempt,
                    self.max_retries + 1,
                    exc,
                )
                if attempt > self.max_retries:
                    break
            except requests.HTTPError as exc:
                self.logger.error(
                    "HTTP error from Ryanair API: %s - response: %s",
                    exc,
                    getattr(exc.response, "text", "")[:500],
                )
                raise RuntimeError(f"Ryanair API responded with an error: {exc}") from exc
            except ValueError as exc:
                self.logger.error("Failed to decode Ryanair API JSON: %s", exc)
                raise RuntimeError("Invalid JSON received from Ryanair API") from exc

        raise RuntimeError(f"Failed to reach Ryanair API after {self.max_retries + 1} attempts: {last_exc}")