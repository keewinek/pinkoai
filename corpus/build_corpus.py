"""Download public-domain verse from Project Gutenberg and clean it into corpus/poetry.txt.

    python3 corpus/build_corpus.py

Keeps only the verse: Gutenberg headers, prose dedications/arguments, headings,
line numbers and footnotes are removed, and typography is folded to plain ASCII.
"""

import re
import sys
import unicodedata
import urllib.request

BOOKS = [
    (1041, "Shakespeare - Sonnets"),
    (1045, "Shakespeare - Venus and Adonis"),
    (1505, "Shakespeare - The Rape of Lucrece"),
    (26, "Milton - Paradise Lost"),
    (8209, "Keats - Poems 1817"),
]

OUT = "corpus/poetry.txt"
ALLOWED = set("\n !'(),-.:;?") | set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Leftover non-verse lines the generic filters can't tell apart from poetry
SKIP_LINES = {"Introduction", "Paradise Lost"}
SKIP_PARAGRAPHS_WITH = ("Vilia miretur",)  # Latin epigraph

TYPOGRAPHY = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "—": "-", "–": "-", "æ": "ae", "Æ": "Ae", "œ": "oe",
}


def fetch(book_id):
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8")


def to_ascii(text):
    for a, b in TYPOGRAPHY.items():
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def is_heading(line):
    s = line.strip()
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters) and len(s) < 60


def clean_line(line):
    line = re.sub(r"\s+\d+\s*$", "", line)      # trailing line numbers
    line = re.sub(r"\[[^\]]*\]?", "", line)     # footnote markers
    line = line.replace("_", "").replace('"', "'")
    return line.strip()


def verse_only(body):
    kept = []
    for para in re.split(r"\n\s*\n", body):
        lines = [clean_line(l) for l in para.split("\n")]
        lines = [l for l in lines if l and not is_heading(l)]
        lines = [l for l in lines if l not in SKIP_LINES]
        if any(m in l for l in lines for m in SKIP_PARAGRAPHS_WITH):
            continue
        # Single lines are titles, bylines and "Book IX" headings, not verse
        if len(lines) < 2:
            continue
        # Prose is wrapped at ~70 columns; verse lines are shorter and ragged
        avg = sum(len(l) for l in lines) / len(lines)
        if avg > 58 or any(len(l) > 75 for l in lines):
            continue
        if any(re.search(r"\d|gutenberg|etext", l, re.I) for l in lines):
            continue
        if any(set(l) - ALLOWED for l in lines):
            continue
        kept.append("\n".join(lines))
    return "\n\n".join(kept)


def main():
    parts = []
    for book_id, title in BOOKS:
        raw = to_ascii(fetch(book_id).replace("\r", ""))
        body = re.split(r"\*\*\* START OF .*?\*\*\*", raw)[1]
        body = re.split(r"\*\*\* END OF", body)[0]
        verse = verse_only(body)
        print(f"{title}: {len(verse)} characters", file=sys.stderr)
        parts.append(verse)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
