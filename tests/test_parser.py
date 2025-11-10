import sys
from pathlib import Path

# Ensure src/ is on the path when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flights.parser import parse_availability_response  # noqa: E402

def _sample_response():
    return {
        "trips": [
            {
                "origin": "VIE",
                "destination": "BCN",
                "dates": [
                    {
                        "dateOut": "2021-05-02T00:00:00.000",
                        "flights": [
                            {
                                "flightNumber": "FR 7350",
                                "timeUTC": [
                                    "2021-05-02T16:55:00.000",
                                    "2021-05-02T19:15:00.000"
                                ],
                                "duration": "02:20",
                                "regularFare": {
                                    "fareClass": "W",
                                    "fares": [
                                        {
                                            "type": "ADT",
                                            "amount": 19.79,
                                            "count": 1,
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

def test_parse_availability_response_basic():
    response = _sample_response()
    result = parse_availability_response(response, max_items=5)

    assert isinstance(result, list)
    assert len(result) == 1

    flight = result[0]
    assert flight["Origin"] == "VIE"
    assert flight["Destination"] == "BCN"
    assert flight["Flight duration"] == "02:20"
    assert flight["Flight number"] == "FR 7350"
    assert flight["Price"] == 19.79
    assert flight["Time departure"] == "2021-05-02T16:55:00.000"
    assert flight["Time arrival"] == "2021-05-02T19:15:00.000"
    assert flight["regularFare"]["fareClass"] == "W"
    assert flight["operatedBy"] == "Buzz"
    assert "scrapedAt" in flight