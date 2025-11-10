from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class FlightSearchQuery:
    origin: str
    destination: str
    date_from: str
    date_to: Optional[str]
    trip_type: str
    adults: int
    teens: int
    children: int
    infants: int
    currency: str
    locale: str
    max_items: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlightSearchQuery":
        def _get(key: str, default=None, required=False):
            if key in data:
                return data[key]
            if required:
                raise ValueError(f"Missing required field '{key}'")
            return default

        origin = str(_get("origin", required=True)).upper()
        destination = str(_get("destination", required=True)).upper()
        date_from = str(_get("dateFrom", required=True))
        date_to = data.get("dateTo")
        trip_type_raw = str(_get("tripType", required=True)).upper().replace("-", "_")
        trip_type = "ROUND_TRIP" if trip_type_raw in {"ROUND_TRIP", "RETURN"} else "ONE_WAY"

        adults = int(_get("adults", 1))
        teens = int(_get("teens", 0))
        children = int(_get("children", 0))
        infants = int(_get("infants", 0))
        currency = str(_get("currency", "EUR")).upper()
        locale = str(_get("locale", "en-gb")).lower()
        max_items_raw = data.get("maxItems")
        max_items = int(max_items_raw) if max_items_raw is not None else None

        _validate_airport_code(origin, "origin")
        _validate_airport_code(destination, "destination")
        _validate_dates(date_from, date_to, trip_type)
        _validate_passengers(adults, teens, children, infants)
        _validate_currency(currency)
        _validate_locale(locale)
        _validate_max_items(max_items)

        return cls(
            origin=origin,
            destination=destination,
            date_from=date_from,
            date_to=date_to,
            trip_type=trip_type,
            adults=adults,
            teens=teens,
            children=children,
            infants=infants,
            currency=currency,
            locale=locale,
            max_items=max_items,
        )

def _validate_airport_code(code: str, field: str) -> None:
    if len(code) != 3 or not code.isalpha():
        raise ValueError(f"Invalid {field} IATA code '{code}', expected 3-letter code.")

def _validate_dates(date_from: str, date_to: Optional[str], trip_type: str) -> None:
    try:
        df = datetime.strptime(date_from, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid dateFrom '{date_from}', expected YYYY-MM-DD.") from exc

    if trip_type == "ROUND_TRIP":
        if not date_to:
            raise ValueError("dateTo is required for ROUND_TRIP searches.")
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Invalid dateTo '{date_to}', expected YYYY-MM-DD.") from exc
        if dt < df:
            raise ValueError("dateTo must be on or after dateFrom for ROUND_TRIP.")

def _validate_passengers(adults: int, teens: int, children: int, infants: int) -> None:
    for name, value in [
        ("adults", adults),
        ("teens", teens),
        ("children", children),
        ("infants", infants),
    ]:
        if value < 0:
            raise ValueError(f"{name} cannot be negative (got {value}).")

    total = adults + teens + children + infants
    if total <= 0:
        raise ValueError("At least one passenger must be specified.")
    if infants > adults:
        raise ValueError("Number of infants cannot exceed number of adults.")

def _validate_currency(currency: str) -> None:
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError(f"Invalid currency '{currency}', expected 3-letter ISO code.")

def _validate_locale(locale: str) -> None:
    if "-" not in locale:
        raise ValueError(f"Invalid locale '{locale}', expected pattern like 'en-gb'.")

def _validate_max_items(max_items: Optional[int]) -> None:
    if max_items is None:
        return
    if max_items <= 0:
        raise ValueError("maxItems must be a positive integer when provided.")