"""Download the corpus pages once and record what was fetched."""

import gzip
import hashlib
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from rag_bakeoff.contracts.raw import RawPage

SITE = "https://www.oesterreich.gv.at"
SITEMAP_URL = f"{SITE}/sitemap.xml"
# The selection recorded in docs/corpus.md.
TOPICS = (
    "familie_und_partnerschaft",
    "arbeit_beruf_und_pension",
    "hilfe_und_finanzielle_unterstuetzung_erhalten",
    "persoenliche_dokumente_und_bestaetigungen",
    "menschen_aus_anderen_staaten",
)
MANIFEST_NAME = "manifest.jsonl"

_LOC = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"


def select_urls(sitemap_xml: bytes, topics: Sequence[str] = TOPICS) -> list[str]:
    """Return the sitemap's page URLs below the given topics, sorted."""
    prefixes = tuple(f"{SITE}/de/themen/{topic}/" for topic in topics)
    urls = {loc.text.strip() for loc in ElementTree.fromstring(sitemap_xml).iter(_LOC) if loc.text}
    return sorted(url for url in urls if url.startswith(prefixes))


def read_manifest(raw_dir: Path) -> list[RawPage]:
    """Return the pages recorded in the raw directory, or none if nothing was fetched yet."""
    manifest = raw_dir / MANIFEST_NAME
    if not manifest.exists():
        return []
    return [RawPage.model_validate_json(line) for line in manifest.read_text().splitlines()]


def fetch_corpus(
    raw_dir: Path,
    *,
    get: Callable[[str], bytes],
    now: Callable[[], datetime],
    pause: Callable[[], None],
) -> list[RawPage]:
    """Fetch every selected page that the manifest does not list yet and return the new entries.

    Each page is recorded as soon as it is stored, so a run that fails part-way can be repeated
    and continues where it stopped.
    """
    already_fetched = {page.url for page in read_manifest(raw_dir)}
    (raw_dir / "pages").mkdir(parents=True, exist_ok=True)
    fetched = []
    for url in select_urls(get(SITEMAP_URL)):
        if url in already_fetched:
            continue
        pause()
        fetched.append(_store(raw_dir, url, get(url), now()))
    return fetched


def _store(raw_dir: Path, url: str, body: bytes, fetched_at: datetime) -> RawPage:
    name = hashlib.sha256(url.encode()).hexdigest()[:16]
    page = RawPage(
        url=url,
        file=f"pages/{name}.html.gz",
        fetched_at=fetched_at,
        sha256=hashlib.sha256(body).hexdigest(),
    )
    # mtime=0 keeps the stored bytes identical for identical pages.
    (raw_dir / page.file).write_bytes(gzip.compress(body, mtime=0))
    with (raw_dir / MANIFEST_NAME).open("a") as manifest:
        manifest.write(page.model_dump_json() + "\n")
    return page
