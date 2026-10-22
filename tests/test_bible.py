"""Looking up entered verses in the bundled texts (no network)."""

import pytest

from daily_verse import bible
from daily_verse.bible import BibleError, Passage


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("Psalm 23:1", Passage(19, 23, 1, 1)),
        ("ps 23:1-3", Passage(19, 23, 1, 3)),
        ("Psalms 23.1", Passage(19, 23, 1, 1)),
        ("1 Cor 13:4–7", Passage(46, 13, 4, 7)),
        ("I Corinthians 13:4", Passage(46, 13, 4, 4)),
        ("1. Korinther 13,4", Passage(46, 13, 4, 4)),
        ("Römer 8,38-39", Passage(45, 8, 38, 39)),
        ("Roemer 8:28", Passage(45, 8, 28, 28)),
        ("Joh 3,16", Passage(43, 3, 16, 16)),
        ("Matth 5:9", Passage(40, 5, 9, 9)),
        ("Jude 24", Passage(65, 1, 24, 24)),
        ("Offb 21:4", Passage(66, 21, 4, 4)),
    ],
)
def test_parse(reference: str, expected: Passage) -> None:
    assert bible.parse(reference) == expected


def test_german_numbering_is_mapped_to_english() -> None:
    # Luther counts the title of Psalm 51 as verses 1-2, and Joel 3 is English 2:28-32.
    assert bible.parse("Psalm 51,12") == Passage(19, 51, 10, 10)
    assert bible.parse("Joel 3,1") == Passage(29, 2, 28, 28)
    with pytest.raises(BibleError, match="title"):
        bible.parse("Psalm 51,1")


@pytest.mark.parametrize(
    ("reference", "message"),
    [
        ("Psalm 23", "add the verse"),
        ("Hezekiah 1:1", "don't know the book"),
        ("Psalm 23:7", "verses 1-6"),
        ("Genesis 51:1", "50 chapters"),
        ("Psalm 119:1-20", "at most"),
        ("23:1", "couldn't read"),
    ],
)
def test_parse_explains_problems(reference: str, message: str) -> None:
    with pytest.raises(BibleError, match=message):
        bible.parse(reference)


def test_english_and_german_text_and_references() -> None:
    passage = bible.parse("Psalm 51:10")
    assert passage.english == "Psalm 51:10"
    assert bible.text("kjv", passage) == "Create in me a clean heart, O God; and renew a right spirit within me."
    assert bible.german_reference(passage) == "Psalm 51,12"
    assert bible.text("lu12", passage).startswith("Schaffe in mir, Gott, ein reines Herz")


def test_psalm_titles_are_left_out() -> None:
    passage = bible.parse("Psalm 23:1")
    assert bible.text("kjv", passage) == "The LORD is my shepherd; I shall not want."
    assert bible.text("lu12", passage) == "Der HERR ist mein Hirte; mir wird nichts mangeln."
    assert bible.german_reference(bible.parse("Psalm 3:1")) == "Psalm 3,2"
    assert bible.text("lu12", bible.parse("Psalm 3:1")).startswith("Ach HERR")


def test_ranges_and_books_with_german_names() -> None:
    passage = bible.parse("Romans 8:38-39")
    assert bible.german_reference(passage) == "Römer 8,38-39"
    assert bible.text("kjv", passage).endswith("which is in Christ Jesus our Lord.")
    assert bible.german_reference(bible.parse("Gen 1:1")) == "1. Mose 1,1"


def test_long_passages_are_refused() -> None:
    bible.check_length(bible.parse("John 3:16"))
    with pytest.raises(BibleError, match="characters"):
        bible.check_length(bible.parse("Esther 8:9"))


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("சங்கீதம் 23:1", "Psalm 23:1"),
        ("சங்கீதங்கள் 23:1-2", "Psalm 23:1-2"),
        ("1 கொரிந்தியர் 13:4", "1 Corinthians 13:4"),
        ("யோவான் 3:16", "John 3:16"),
        ("3 யோவான் 1:2", "3 John 1:2"),
        ("வெளிப்படுத்தின விசேஷம் 21:4", "Revelation 21:4"),
        ("ரோமர் 8:28", "Romans 8:28"),
    ],
)
def test_tamil_book_names(reference: str, expected: str) -> None:
    assert bible.parse(reference).english == expected


def test_every_tamil_name_is_its_own_book() -> None:
    assert len(bible.TAMIL_BOOKS) == 66
    assert [bible.find_book(name) for name in bible.TAMIL_BOOKS] == list(range(1, 67))

