"""Entering the day's verse."""

from datetime import date
import importlib
import json
from pathlib import Path

import pytest

from daily_verse import sources


@pytest.fixture
def main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path))
    module = importlib.reload(importlib.import_module("daily_verse.__main__"))
    made = []
    monkeypatch.setattr(module.render, "render", lambda verse, day, out, *a, **k: made.append(out.name) or out)
    monkeypatch.setattr(module, "render_language_video", lambda verse, day, out, *a, **k: made.append(out.name))
    monkeypatch.setattr(module.imagery, "scene_for", lambda *a, **k: None)
    module.made = made
    return module


def test_a_verse_makes_pictures_and_videos_in_both_languages(main, tmp_path: Path, monkeypatch) -> None:
    verses = {"ta": sources.Verse("ta", "சங்கீதம் 23:1", "கர்த்தர் என் மேய்ப்பராயிருக்கிறார்"),
              "en": sources.Verse("en", "Psalm 23:1", "The LORD is my shepherd")}
    monkeypatch.setattr(main.sources, "fetch_custom", lambda ref, topics: (verses, topics))
    args = type("A", (), {"reference": "psalm 23,1", "theme": "rest, trust", "date": date(2026, 10, 23)})
    assert main.cmd_verse(args) == 0
    assert main.made == ["23-ta.png", "23-ta.mp4", "23-en.png", "23-en.mp4"]
    manifest = json.loads((tmp_path / "2026/10/23.json").read_text(encoding="utf-8"))
    assert manifest["reference"] == "Psalm 23:1" and manifest["topics"] == ["rest", "trust"]
    assert set(manifest["verses"]) == {"ta", "en"} and manifest["revision"] == 0
    assert main.cmd_verse(args) == 0  # entered again the same day: replaced, with new links
    assert json.loads((tmp_path / "2026/10/23.json").read_text(encoding="utf-8"))["revision"] == 1


def test_an_unknown_reference_fails_without_making_anything(main, monkeypatch) -> None:
    def refuse(ref, topics):
        raise sources.SourceError("I don't know the book “Psalmz”")

    monkeypatch.setattr(main.sources, "fetch_custom", refuse)
    args = type("A", (), {"reference": "Psalmz 23:1", "theme": "", "date": date(2026, 10, 23)})
    assert main.cmd_verse(args) == 1 and main.made == []
