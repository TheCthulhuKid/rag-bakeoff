import gzip
import hashlib
from datetime import UTC, datetime

import httpx
import pytest

from rag_bakeoff.cli import main
from rag_bakeoff.corpus.fetch import SITE, SITEMAP_URL, fetch_corpus, read_manifest, select_urls

PASS = f"{SITE}/de/themen/persoenliche_dokumente_und_bestaetigungen/reisepass/Seite.020100"
BIRTH = f"{SITE}/de/themen/familie_und_partnerschaft/geburt/Seite.080100"
TAX = f"{SITE}/de/themen/steuern_und_finanzen/Seite.340000"
SITEMAP = (
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    + "".join(f"<url><loc>{url}</loc></url>" for url in (PASS, BIRTH, TAX))
    + "</urlset>"
).encode()
PAGES = {SITEMAP_URL: SITEMAP, PASS: b"<p>Reisepass</p>", BIRTH: b"<p>Geburt</p>"}
NOON = datetime(2026, 11, 23, 12, tzinfo=UTC)


def fetch(raw_dir, pages=PAGES):
    return fetch_corpus(raw_dir, get=pages.__getitem__, now=lambda: NOON, pause=lambda: None)


def test_only_pages_of_the_chosen_topics_are_selected():
    assert select_urls(SITEMAP) == [BIRTH, PASS]


def test_fetch_stores_each_page_with_its_hash_in_the_manifest(tmp_path):
    fetch(tmp_path)
    page = read_manifest(tmp_path)[1]
    assert (page.url, page.fetched_at) == (PASS, NOON)
    assert gzip.decompress((tmp_path / page.file).read_bytes()) == PAGES[PASS]
    assert page.sha256 == hashlib.sha256(PAGES[PASS]).hexdigest()


def test_rerun_after_a_failure_fetches_only_the_missing_pages(tmp_path):
    without_pass = {url: body for url, body in PAGES.items() if url != PASS}
    with pytest.raises(KeyError):
        fetch(tmp_path, without_pass)
    assert [page.url for page in fetch(tmp_path)] == [PASS]
    assert [page.url for page in read_manifest(tmp_path)] == [BIRTH, PASS]


def test_fetch_command_downloads_the_selected_pages(tmp_path, capsys):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=PAGES[str(request.url)])
    )
    main(["fetch", "--raw-dir", str(tmp_path), "--pause", "0"], transport=transport)
    assert "Fetched 2 new pages, 2 in" in capsys.readouterr().out


def test_fetch_command_stops_on_a_page_the_site_does_not_serve(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        main(["fetch", "--raw-dir", str(tmp_path), "--pause", "0"], transport=transport)
