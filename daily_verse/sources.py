"""Fetch the verse the ministry entered, in its languages (church.json "languages").

English (King James Version) and German (Lutherbibel 1912) come from the bundled
public-domain texts (bible.py). The Tamil text of the same passage comes from
tamil-bible.com, which follows the English verse numbering.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
import time
import urllib.request

from . import bible
from .config import ORDER

TAMIL_BIBLE = "https://www.tamil-bible.com"
USER_AGENT = "rise-shine-verse/1.0 (+https://github.com/franklinis/rise-shine-verse)"

# Book parameters used by tamil-bible.com's lookup.php, in canonical order.
TAMIL_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Ruth", "I_Samuel", "II_Samuel", "I_Kings", "II_Kings", "I_Chronicles",
    "II_Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song_of_Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel",
    "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John",
    "Acts", "Romans", "I_Corinthians", "II_Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "I_Thessalonians", "II_Thessalonians", "I_Timothy",
    "II_Timothy", "Titus", "Philemon", "Hebrews", "James", "I_Peter", "II_Peter",
    "I_John", "II_John", "III_John", "Jude", "Revelation",
]

class SourceError(Exception):
    """A source page was missing or did not look as expected."""


@dataclass(frozen=True)
class Verse:
    """One language's slide: display reference and text."""

    lang: str
    reference: str
    text: str


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
    time.sleep(1)  # Be gentle with small, volunteer-run sites.
    return body


def clean(fragment: str) -> str:
    """Turn a verse's HTML into plain text, keeping KJV's small-caps LORD."""
    fragment = re.sub(
        r'<span[^>]*small-caps[^>]*>(.*?)</span>',
        lambda m: m.group(1).upper(),
        fragment,
        flags=re.S,
    )
    fragment = re.sub(r"<br\s*/?>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


ROMAN = {"I": "1", "II": "2", "III": "3"}


def tamil_book_name(name: str) -> str:
    """tamil-bible.com writes numbered books with Roman numerals ("I கொரிந்தியர்"); Tamil Bibles write "1 கொரிந்தியர்"."""
    return re.sub(r"^(III|II|I)\s+", lambda m: ROMAN[m[1]] + " ", name.strip())


def parse_tamil(page: str, chapter: int, first: int, last: int) -> tuple[str, str]:
    """Return (Tamil reference, text) for verses first..last of a chapter page."""
    title = re.search(r"<title>\s*(.+?)\s+\d+\s+—", page, re.S)
    if not title:
        raise SourceError("tamil-bible.com page layout changed: book name not found")
    texts = []
    for number in range(first, last + 1):
        match = re.search(
            rf'<div class="verse-row" id="v{number}">.*?<div class="verse-tamil">(.*?)</div>',
            page,
            re.S,
        )
        if not match:
            raise SourceError(f"tamil-bible.com has no verse {chapter}:{number}")
        text = clean(match.group(1))
        if number == 1:
            text = re.sub(r"^\([^)]*\)\s*", "", text)  # a psalm's title, e.g. "(தாவீதின் சங்கீதம்.)"
        texts.append(text)
    verses = str(first) if first == last else f"{first}-{last}"
    return f"{tamil_book_name(html.unescape(title.group(1)))} {chapter}:{verses}", " ".join(texts)


def fetch_custom(reference: str, topics: list[str] | None = None) -> tuple[dict[str, Verse], list[str]]:
    """The verse entered, e.g. "Psalm 23:1", in each configured language, with its theme words."""
    try:
        passage = bible.parse(reference)
        bible.check_length(passage)
    except bible.BibleError as err:
        raise SourceError(str(err)) from err
    verses = {}
    if "ta" in ORDER:
        ta_ref, ta_text = parse_tamil(
            _get(f"{TAMIL_BIBLE}/lookup.php?Book={TAMIL_BOOKS[passage.book - 1]}&Chapter={passage.chapter}"),
            passage.chapter,
            passage.first,
            passage.last,
        )
        verses["ta"] = Verse("ta", ta_ref, ta_text)
    if "en" in ORDER:
        verses["en"] = Verse("en", passage.english, bible.text("kjv", passage))
    if "de" in ORDER:
        verses["de"] = Verse("de", bible.german_reference(passage), bible.text("lu12", passage))
    return verses, list(topics or [])
