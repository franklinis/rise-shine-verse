"""The ministry's settings (church.json): name, languages, titles, voices and image style."""

from __future__ import annotations

import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parent.parent
CHURCH = json.loads((ROOT / "church.json").read_text(encoding="utf-8"))
ORDER: tuple[str, ...] = tuple(CHURCH["languages"])
# Mixed into every date-based choice (palette, art direction, drawn mountains, music), so this ministry's
# days never look or sound like another project's that shares the same code (e.g. the church's daily verse).
VARIETY = zlib.crc32(CHURCH.get("variety", "").encode()) % 100_000
