"""The download and WhatsApp Status page."""

from datetime import date
import json
from pathlib import Path
import re

from daily_verse import status_page

VERSES = {
    "ta": {"lang": "ta", "reference": "சங்கீதம் 119:14", "text": "களிகூருகிறேன்."},
    "en": {"lang": "en", "reference": "Psalm 119:14", "text": "I have rejoiced </script>."},
}


def _manifest(media: Path, day: str, **extra: object) -> None:
    path = media / f"{day[:4]}/{day[5:7]}/{day[8:]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    files = {"images": {lang: f"{day[:4]}/{day[5:7]}/{day[8:]}-{lang}.png" for lang in VERSES},
             "videos": {lang: f"{day[:4]}/{day[5:7]}/{day[8:]}-{lang}.mp4" for lang in VERSES}}
    path.write_text(json.dumps({"date": day, "verses": VERSES, **files, **extra}, ensure_ascii=False))


def test_page_lists_the_latest_days_with_pictures_and_videos(tmp_path: Path) -> None:
    _manifest(tmp_path, "2026-10-14")
    _manifest(tmp_path, "2026-10-15", revision=2)
    page = status_page.build(tmp_path, date(2026, 10, 15)).read_text(encoding="utf-8")
    raw = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S)[1]
    assert "</script>" not in raw  # the verse text cannot break out of the data block
    data = json.loads(raw.replace("<\\/", "</"))
    assert [d["date"] for d in data["days"]] == ["2026-10-15", "2026-10-14"]  # newest first
    tamil = data["days"][0]["items"][0]
    assert tamil["video"] == "2026/10/15-ta.mp4?v=2" and tamil["image"] == "2026/10/15-ta.png?v=2"
    assert tamil["language"] == "தமிழ்" and tamil["image_filename"] == "verse-2026-10-15-ta.png"
    assert tamil["caption"] == "இன்றைய வசனம் · சங்கீதம் 119:14\nRise & Shine Ministries"
    assert "Rise &amp; Shine Ministries" in page and not re.findall(r"__[A-Z]+__", page)
    assert (tmp_path / "icon.png").exists() and (tmp_path / ".nojekyll").exists()
    assert json.loads((tmp_path / "manifest.webmanifest").read_text())["short_name"] == "Verse of the Day"


def test_the_form_is_published_with_its_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FORM_ENDPOINT", "https://example.logic.azure.com/workflows/x?sig=abc")
    status_page.build(tmp_path, date(2026, 10, 15))
    form = (tmp_path / "form" / "index.html").read_text(encoding="utf-8")
    assert 'const ENDPOINT = "https://example.logic.azure.com/workflows/x?sig=abc";' in form
    assert "repos/franklinis/rise-shine-verse/actions/workflows/verse.yml/runs" in form
    assert not re.findall(r"__[A-Z]+__", form)  # every placeholder filled in

