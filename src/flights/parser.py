from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _extract_price(flight: Dict[str, Any]) -> Optional[float]:
    fare = flight.get("regularFare") or {}
    fares = fare.get("fares") or []
    if not fares:
        return None
    amount = fares[0].get("amount")
    try:
        return float(amount)
    except (TypeError, ValueError):
        return None

def parse_availability_response(
    response: Dict[str, Any],
    max_items: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Normalize Ryanair availability payload into a flat list of flight dicts.

    Expected (simplified) response schema:

    {
      "trips": [
        {
          "origin": "VIE",
          "destination": "BCN",
          "dates": [
            {
              "dateOut": "2021-05-02T00:00:00.000",
              "flights": [
                {
                  "flightNumber": "FR7350",
                  "timeUTC": ["2021-05-02T16:55:00.000Z", "2021-05-02T19:15:00.000Z"],
                  "duration": "02:20",
                  "regularFare": {...},
                  "operatedBy": "Buzz",
                  "key": "..."
                }
              ]
            }
          ]
        }
      ]
    }
    """
    results: List[Dict[str, Any]] = []
    scraped_at = _utc_now_iso()

    for trip in response.get("trips", []):
        origin = trip.get("origin")
        destination = trip.get("destination")
        for date_block in trip.get("dates", []):
            for flight in date_block.get("flights", []):
                time_utc = flight.get("timeUTC") or []
                time_departure = time_utc[0] if len(time_utc) > 0 else None
                time_arrival = time_utc[1] if len(time_utc) > 1 else None

                item = {
                    "Origin": origin,
                    "Destination": destination,
                    "Flight duration": flight.get("duration"),
                    "Flight number": flight.get("flightNumber"),
                    "Price": _extract_price(flight),
                    "Time departure": time_departure,
                    "Time arrival": time_arrival,
                    "key": flight.get("key"),
                    "scrapedAt": scraped_at,
                    "regularFare": flight.get("regularFare"),
                    "operatedBy": flight.get("operatedBy"),
                }
                results.append(item)

                if max_items is not None and len(results) >= max_items:
                    return results

    return results