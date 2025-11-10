import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure src/ is on the path when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from main import run_search  # noqa: E402

class DummyClient:
    def __init__(self, base_url: str, timeout: int, proxies, logger) -> None:  # noqa: D401
        self.base_url = base_url
        self.timeout = timeout
        self.proxies = proxies
        self.logger = logger

    def search_flights(self, query) -> Dict[str, Any]:  # noqa: D401
        # Simple deterministic payload to exercise parser + exporter
        return {
            "trips": [
                {
                    "origin": query.origin,
                    "destination": query.destination,
                    "dates": [
                        {
                            "dateOut": f"{query.date_from}T00:00:00.000",
                            "flights": [
                                {
                                    "flightNumber": "FR 7350",
                                    "timeUTC": [
                                        f"{query.date_from}T16:55:00.000",
                                        f"{query.date_from}T19:15:00.000"
                                    ],
                                    "duration": "02:20",
                                    "regularFare": {
                                        "fareClass": "W",
                                        "fares": [
                                            {
                                                "type": "ADT",
                                                "amount": 19.79,
                                                "count": query.adults,
                                                "hasDiscount": True
                                            }
                                        ]
                                    },
                                    "operatedBy": "Buzz",
                                    "key": "FR~7350~ ~~VIE~05/02/2021 16:55~BCN~05/02/2021 19:15~~"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

def test_run_search_end_to_end(tmp_path: Path):
    settings = {
        "baseUrl": "https://example.test/availability",
        "timeoutSeconds": 5,
        "proxyUrl": "http://user:pass@proxy:8080"
    }
    search_input = {
        "origin": "VIE",
        "destination": "BCN",
        "dateFrom": "2021-05-02",
        "dateTo": "2021-05-02",
        "tripType": "ONE_WAY",
        "adults": 1,
        "teens": 0,
        "children": 0,
        "infants": 0,
        "currency": "EUR",
        "locale": "en-gb",
        "maxItems": 3
    }

    output_path = tmp_path / "flights.json"

    flights = run_search(search_input, settings, output_path, client_cls=DummyClient)

    assert output_path.is_file()
    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["Origin"] == "VIE"
    assert data[0]["Destination"] == "BCN"
    assert flights[0]["Flight number"] == "FR 7350"