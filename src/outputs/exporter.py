from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, List

def export_to_json(data: Iterable[Any], output_path: Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # materialize iterable to list for JSON serialization
    payload: List[Any] = list(data)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)