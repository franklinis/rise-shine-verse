"""Command line: make the day's slides and videos from the verse the ministry entered.

    python -m daily_verse verse --reference "Psalm 23:1" [--theme "trust, rest"] [--date YYYY-MM-DD]
    python -m daily_verse redo --date YYYY-MM-DD        (a new background for that day)
    python -m daily_verse prune [--keep-days N]
    python -m daily_verse page                           (the download and WhatsApp Status page)

Each day gets YYYY/MM/DD-{ta,en}.png (feed pictures), YYYY/MM/DD-{ta,en}.mp4
(vertical videos for Reels, Shorts and WhatsApp Status) and a DD.json manifest
in $MEDIA_DIR (default ./images). Entering a verse again for the same day
replaces that day.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import sys
import tempfile
from zoneinfo import ZoneInfo

from . import imagery, music, render, sources, speech, status_page, video
from .config import ORDER

IMAGES = Path(os.environ.get("MEDIA_DIR", render.ROOT / "images"))
TIMEZONE = ZoneInfo("Europe/Berlin")


def manifest_path(day: date) -> Path:
    return IMAGES / f"{day:%Y/%m/%d}.json"


def image_name(day: date, lang: str) -> str:
    return f"{day:%Y/%m/%d}-{lang}.png"


def language_video_name(day: date, lang: str) -> str:
    return f"{day:%Y/%m/%d}-{lang}.mp4"


def narration_on() -> bool:
    """Read-aloud is used once NARRATION is "on" and Azure Speech is configured."""
    return os.environ.get("NARRATION", "").lower() == "on" and speech.enabled()


def render_language_video(
    verse: sources.Verse, day: date, out: Path, narrate: bool, scene: Path | None = None
) -> bool:
    """One vertical slide with music (and the reading, if narrated); returns whether it is narrated."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        voice = timeline = None
        if narrate:
            # Follow-along: each word lights up as it is read.
            looks = render.render_highlight(verse, day, work / "looks", scene)
            slide = looks["bright"]
            reading = speech.narrate_one(verse.lang, asdict(verse), day, work)
            seconds, starts = video.narrated_timing([reading.seconds])
            voice = speech.combine([reading], starts, seconds[0], work / "narration.wav")
            times = [(starts[0] + a, starts[0] + b) for a, b in speech.word_times(reading, verse.text)]
            print(f"{day} {verse.lang}: {reading.voice}, {reading.seconds:.1f}s, "
                  f"{speech.LAST_MATCHED}/{len(times)} words on screen timed by Azure")
            timeline = video.highlight_timeline(looks, times, seconds[0], work / "frames")
        else:
            slide = render.render(verse, day, work / f"{verse.lang}.png", "video", scene)
            seconds = [video.reading_seconds(verse.text) + 1.5]
        track, _ = music.track_for(day, seconds[0], work)
        video.make_video([slide], seconds, out, music=track, narration=voice, timeline=timeline)
    return voice is not None


def make_day(day: date, verses: dict[str, sources.Verse], topics: list[str], new_background: bool,
             reference: str | None = None) -> dict:
    """Render the pictures and videos for a day and write its manifest."""
    path = manifest_path(day)
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if new_background or old.get("reference") != reference:
        (IMAGES / imagery.scene_name(day)).unlink(missing_ok=True)  # a background for this verse
    scene = imagery.scene_for(day, {lang: asdict(verses[lang]) for lang in ORDER}, topics, IMAGES)
    narrate = narration_on()
    manifest = {
        "date": day.isoformat(),
        "reference": reference or old.get("reference"),
        "verses": {lang: asdict(verses[lang]) for lang in ORDER},
        "topics": topics,
        "images": {lang: image_name(day, lang) for lang in ORDER},
        "videos": {lang: language_video_name(day, lang) for lang in ORDER},
        "scene": imagery.scene_name(day) if scene else None,
        "narrated": narrate,
        # New links whenever a day is made again, so no phone shows the old files.
        "revision": old.get("revision", 0) + 1 if old else 0,
    }
    for lang in ORDER:
        render.render(verses[lang], day, IMAGES / image_name(day, lang), scene=scene)
        render_language_video(verses[lang], day, IMAGES / language_video_name(day, lang), narrate, scene)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def cmd_verse(args: argparse.Namespace) -> int:
    day = args.date or datetime.now(TIMEZONE).date()
    topics = [t.strip() for t in args.theme.split(",") if t.strip()]
    try:
        verses, topics = sources.fetch_custom(args.reference, topics)
    except sources.SourceError as err:
        print(f"::error::{err}")
        return 1
    make_day(day, verses, topics, new_background=False, reference=verses["en" if "en" in ORDER else ORDER[0]].reference)
    print(f"{day}: " + " · ".join(verses[lang].reference for lang in ORDER))
    return 0


def cmd_redo(args: argparse.Namespace) -> int:
    """A new verse-matched background for a day, then its pictures and videos again."""
    if not imagery.enabled():
        print("::error::Set BACKGROUNDS=ai and the Azure image settings to make new backgrounds")
        return 2
    day = args.date or datetime.now(TIMEZONE).date()
    path = manifest_path(day)
    if not path.exists():
        print(f"::error::{day} has no verse yet")
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8"))
    verses = {lang: sources.Verse(**manifest["verses"][lang]) for lang in ORDER}
    make_day(day, verses, manifest.get("topics", []), new_background=True, reference=manifest.get("reference"))
    print(f"{day}: new background")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    """Delete days older than --keep-days, so the media branch stays small."""
    cutoff = datetime.now(TIMEZONE).date() - timedelta(days=args.keep_days)
    for path in sorted(IMAGES.glob("*/*/*")):
        try:
            day = date(int(path.parts[-3]), int(path.parts[-2]), int(path.name[:2]))
        except ValueError:
            continue
        if day < cutoff:
            path.unlink()
    for folder in sorted(IMAGES.glob("*/*"), reverse=True) + sorted(IMAGES.glob("*"), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    return 0


def cmd_page(args: argparse.Namespace) -> int:
    page = status_page.build(IMAGES, datetime.now(TIMEZONE).date())
    print(f"Page: {page}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="daily_verse")
    parser.add_argument("command", choices=["verse", "redo", "prune", "page"])
    parser.add_argument("--reference", default="", help='the verse, e.g. "Psalm 23:1" or "Römer 8,28"')
    parser.add_argument("--theme", default="", help="optional words that steer the background, e.g. hope, trust")
    parser.add_argument("--date", type=lambda s: date.fromisoformat(s) if s else None, default=None,
                        help="the day (default: today in Munich)")
    parser.add_argument("--keep-days", type=int, default=30)
    args = parser.parse_args()
    if args.command == "verse" and not args.reference.strip():
        parser.error("verse needs --reference")
    commands = {"verse": cmd_verse, "redo": cmd_redo, "prune": cmd_prune, "page": cmd_page}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
