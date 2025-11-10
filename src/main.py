import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from flights.validator import FlightSearchQuery
from flights.api_client import RyanairApiClient
from flights.parser import parse_availability_response
from outputs.exporter import export_to_json
from utils.logger import get_logger
from utils.proxy_manager import build_proxies

DEFAULT_BASE_URL = "https://www.ryanair.com/api/booking/v4/en-gb/availability"

def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _resolve_default_paths() -> Dict[str, Path]:
    root = Path(__file__).resolve().parents[1]
    src_dir = Path(__file__).resolve().parent
    config_path = src_dir / "config" / "settings.example.json"
    input_path = root / "data" / "sample_input.json"
    output_path = root / "data" / "sample_output.json"
    return {
        "config": config_path,
        "input": input_path,
        "output": output_path,
    }

def run_search(
    search_input: Dict[str, Any],
    settings: Dict[str, Any],
    output_path: Path,
    client_cls=RyanairApiClient,
) -> List[Dict[str, Any]]:
    logger = get_logger("ryanair_scraper")
    logger.info("Starting Ryanair flights search")

    query = FlightSearchQuery.from_dict(search_input)

    base_url = settings.get("baseUrl", DEFAULT_BASE_URL)
    timeout = int(settings.get("timeoutSeconds", 10))
    proxy_url = settings.get("proxyUrl")
    proxies = build_proxies(proxy_url) if proxy_url else None

    client = client_cls(base_url=base_url, timeout=timeout, proxies=proxies, logger=logger)

    try:
        raw_response = client.search_flights(query)
    except Exception as exc:  # pragma: no cover - top-level guard
        logger.error("Failed to fetch flights: %s", exc)
        raise

    flights = parse_availability_response(raw_response, max_items=query.max_items)
    export_to_json(flights, output_path)

    logger.info("Completed search: %d flights exported to %s", len(flights), output_path)
    return flights

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ryanair flights scraper - fetches live flight data and exports JSON."
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to settings JSON file (default: src/config/settings.example.json)",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to flight search input JSON (default: data/sample_input.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output JSON file (default: data/sample_output.json)",
    )
    return parser

def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    defaults = _resolve_default_paths()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config) if args.config else defaults["config"]
    input_path = Path(args.input) if args.input else defaults["input"]
    output_path = Path(args.output) if args.output else defaults["output"]

    try:
        settings = _load_json(config_path)
    except Exception as exc:
        print(f"Error loading settings from {config_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        search_input = _load_json(input_path)
    except Exception as exc:
        print(f"Error loading search input from {input_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        run_search(search_input, settings, output_path)
    except Exception as exc:
        print(f"Scraper failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()