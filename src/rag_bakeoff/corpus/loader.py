"""Turn the fetched raw pages into the normalised documents every run uses."""

import gzip
import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Comment, Tag

from rag_bakeoff.contracts.document import Document
from rag_bakeoff.contracts.raw import RawPage
from rag_bakeoff.corpus.fetch import SITE, read_manifest

TOPIC_ROOT = f"{SITE}/de/themen/"
# English pages inside the German corpus, see docs/corpus.md.
ENGLISH_SECTION = "menschen_aus_anderen_staaten/Information-in-English"

_BLOCKS = ["h2", "h3", "h4", "p", "li", "tr"]
_MARKS = {"h2": "## ", "h3": "### ", "h4": "#### ", "li": "- "}
_INLINE = ["a", "span", "abbr", "strong", "em", "mark", "sup"]
_NOT_TEXT = ["template", "svg", "button", "img"]
# "<label>: 08.01.2026 <label>: <owner>". The labels are not matched, as a few pages have them
# in English.
_FOOTER = re.compile(r".+?: (\d\d)\.(\d\d)\.(\d{4}) .+?: (.+)")


@dataclass(frozen=True)
class LoadResult:
    """The loaded documents, and how many pages were left out for which reason."""

    documents: list[Document]
    dropped: Counter[str]


def load_documents(raw_dir: Path) -> LoadResult:
    """Parse every page in the manifest into a document, sorted by ID.

    Raises ValueError if the stored pages do not match the manifest, so a changed or stray file
    cannot slip into a run unnoticed.
    """
    pages = read_manifest(raw_dir)
    stored = {path.relative_to(raw_dir).as_posix() for path in (raw_dir / "pages").iterdir()}
    if stray := stored - {page.file for page in pages}:
        raise ValueError(f"raw files missing from the manifest: {sorted(stray)}")
    documents = []
    dropped: Counter[str] = Counter()
    for page in pages:
        html = _read(raw_dir, page)
        if ENGLISH_SECTION in page.url:
            dropped["english"] += 1
        elif document := parse_page(html, page):
            documents.append(document)
        else:
            dropped["link list"] += 1
    return LoadResult(sorted(documents, key=lambda document: document.id), dropped)


def write_documents(documents: list[Document], path: Path) -> None:
    """Write the documents as JSONL, one per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(document.model_dump_json() + "\n" for document in documents))


def parse_page(html: bytes, page: RawPage) -> Document | None:
    """Extract the document from one page, or None if the page only lists links."""
    sections = BeautifulSoup(html, "html.parser").select("#content > .content-page > div")
    if len(sections) < 3 or not sections[0].h1:
        raise ValueError(f"unexpected page layout: {page.url}")
    title, body, footer = sections[:3]
    updated = _FOOTER.fullmatch(footer.get_text(" ", strip=True))
    if not updated:
        raise ValueError(f"no last-updated date and owner found: {page.url}")
    if _is_link_list(body):
        return None
    day, month, year, owner = updated.groups()
    doc_id = page.url.removeprefix(TOPIC_ROOT)
    return Document(
        id=doc_id,
        title=title.h1.get_text(" ", strip=True),
        url=page.url,
        text=_text(body),
        metadata={
            "topic": doc_id.split("/")[0],
            "last_updated": f"{year}-{month}-{day}",
            "owner": owner,
            "fetched_at": page.fetched_at.isoformat(),
        },
    )


def _read(raw_dir: Path, page: RawPage) -> bytes:
    html = gzip.decompress((raw_dir / page.file).read_bytes())
    if hashlib.sha256(html).hexdigest() != page.sha256:
        raise ValueError(f"raw file changed since it was fetched: {page.file}")
    return html


def _is_link_list(body: Tag) -> bool:
    """Whether the body is navigation: mostly bare links, with no more than a teaser beside them."""
    blocks = [block for block in body.find_all(_BLOCKS) if not block.find(_BLOCKS)]
    other = [block for block in blocks if not _is_bare_link(block)]
    links = len(blocks) - len(other)
    return links > len(other) and sum(len(block.get_text(strip=True)) for block in other) < 400


def _is_bare_link(block: Tag) -> bool:
    return block.a is not None and block.get_text(strip=True) == block.a.get_text(strip=True)


def _text(body: Tag) -> str:
    """Return the body as plain text: one line per block, headings and list items marked."""
    for element in body.find_all(_NOT_TEXT):
        element.decompose()
    # Comments and inline tags split a sentence into several strings, which would become lines.
    for comment in body.find_all(string=lambda string: isinstance(string, Comment)):
        comment.extract()
    for element in body.find_all(_INLINE):
        element.unwrap()
    body.smooth()
    for row in body.find_all("tr"):
        row.string = " | ".join(
            cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])
        )
    for name, mark in _MARKS.items():
        for element in body.find_all(name):
            if first := next(element.stripped_strings, None):
                element.find(string=lambda string: string.strip() == first).replace_with(
                    mark + first
                )
    return "\n".join(" ".join(line.split()) for line in body.stripped_strings)
