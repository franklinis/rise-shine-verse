"""The ministry's settings (church.json): name, languages, titles, voices and image style."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHURCH = json.loads((ROOT / "church.json").read_text(encoding="utf-8"))
ORDER: tuple[str, ...] = tuple(CHURCH["languages"])
