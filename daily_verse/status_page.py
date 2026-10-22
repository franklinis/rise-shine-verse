"""The phone page with each day's pictures and videos: download them, or share a video to WhatsApp Status.

WhatsApp has no official way to post a Status automatically, so each video gets
a button that opens the phone's share sheet with the video attached (choose
WhatsApp → My status), plus a caption to copy. It is written into the media
folder, which GitHub Pages serves at https://franklinis.github.io/rise-shine-verse/.
"""

from __future__ import annotations

from datetime import date
import html
import json
import os
from pathlib import Path

from .config import CHURCH, ROOT

LANGUAGE_NAMES = {"ta": "தமிழ்", "en": "English", "de": "Deutsch"}
TEMPLATE = (Path(__file__).parent / "status_page.html").read_text(encoding="utf-8")
FORM = (Path(__file__).parent / "form.html").read_text(encoding="utf-8")


def caption(manifest: dict, lang: str) -> str:
    """The Status text: label and reference, then the website."""
    reference = manifest["verses"][lang]["reference"]
    website = CHURCH.get("website", "").removeprefix("https://")
    return f"{CHURCH['label'][lang]} · {reference}\n{website or CHURCH['name']}"


def collect(media: Path) -> list[dict]:
    """The latest days with videos, newest first."""
    days = []
    for path in sorted(media.glob("*/*/*.json"), reverse=True)[:7]:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        videos = manifest.get("videos") or {}
        if not videos:
            continue
        version = f"?v={manifest['revision']}" if manifest.get("revision") else ""
        days.append({
            "date": manifest["date"],
            "items": [
                {
                    "lang": lang,
                    "language": LANGUAGE_NAMES[lang],
                    "reference": manifest["verses"][lang]["reference"],
                    "video": name + version,
                    "filename": f"verse-{manifest['date']}-{lang}.mp4",
                    "image": manifest["images"][lang] + version,
                    "image_filename": f"verse-{manifest['date']}-{lang}.png",
                    "caption": caption(manifest, lang),
                }
                for lang, name in videos.items()
            ],
        })
    return days


def _icon(out: Path) -> None:
    """Home-screen icon: the white logo on the page colour."""
    from PIL import Image

    logo = Image.open(ROOT / "assets" / "logo-white.png").convert("RGBA").resize((400, 400), Image.LANCZOS)
    icon = Image.new("RGBA", (512, 512), CHURCH["page"]["card"])
    icon.alpha_composite(logo, (56, 56))
    icon.convert("RGB").save(out)


def _themed(template: str) -> str:
    colours = CHURCH["page"]
    return (template.replace("__NAME__", html.escape(CHURCH["name"]))
            .replace("__BACKGROUND__", colours["background"]).replace("__CARD__", colours["card"])
            .replace("__ACCENT__", colours["accent"]))


def build(media: Path, today: date | None = None) -> Path:
    """Write index.html (with the days embedded), the icon and the web app manifest into `media`."""
    media.mkdir(parents=True, exist_ok=True)
    data = json.dumps({"days": collect(media), "built": (today or date.today()).isoformat()}, ensure_ascii=False)
    # Keep the embedded JSON from ever closing the <script> tag early.
    page = _themed(TEMPLATE).replace("__DATA__", data.replace("</", "<\\/"))
    (media / "index.html").write_text(page, encoding="utf-8")
    # The team's form for entering the verse; FORM_ENDPOINT is the Azure Logic App's URL.
    (media / "form").mkdir(exist_ok=True)
    form = _themed(FORM).replace("__ENDPOINT__", os.environ.get("FORM_ENDPOINT", "")).replace(
        "__REPO__", CHURCH["repository"])
    (media / "form" / "index.html").write_text(form, encoding="utf-8")
    _icon(media / "icon.png")
    (media / "manifest.webmanifest").write_text(json.dumps({
        "name": f"Verse of the Day · {CHURCH['name']}",
        "short_name": "Verse of the Day",
        "start_url": ".",
        "display": "standalone",
        "background_color": CHURCH["page"]["background"],
        "theme_color": CHURCH["page"]["card"],
        "icons": [{"src": "icon.png", "sizes": "512x512", "type": "image/png"}],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (media / ".nojekyll").write_text("")  # serve files as they are
    return media / "index.html"
