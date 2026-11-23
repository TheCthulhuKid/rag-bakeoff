from datetime import UTC, datetime

import pytest

from rag_bakeoff.cli import main
from rag_bakeoff.corpus.fetch import SITEMAP_URL, fetch_corpus, read_manifest
from rag_bakeoff.corpus.loader import TOPIC_ROOT, load_documents

FOOTER = "Letzte Aktualisierung: 08.01.2026 Für den Inhalt verantwortlich: Bundeskanzleramt"
PASSPORT = (
    "<h2>Kosten</h2><p>Der <a href='/pass'>Reisepass</a> kostet <!-- --><span>112 Euro</span>.</p>"
    "<ul><li>Passfoto</li></ul><table><tr><th>Alter</th><td>ab 12</td></tr></table>"
)
LINKS = (
    "<ul><li><a href='/a'>Antrag</a></li><li><a href='/b'>Kosten</a></li></ul><p>Infos zum Pass</p>"
)
BODIES = {
    "persoenliche_dokumente_und_bestaetigungen/reisepass/Seite.1": PASSPORT,
    "persoenliche_dokumente_und_bestaetigungen/reisepass": LINKS,
    "menschen_aus_anderen_staaten/Information-in-English/Work": "<p>Work in Austria</p>",
}


def raw_dir_with(tmp_path, bodies=BODIES):
    pages = {
        TOPIC_ROOT + path: (
            f'<div id="content"><div class="content-page"><div><h1>Reisepass</h1></div>'
            f"<div>{body}</div><div>{FOOTER}</div></div></div>"
        ).encode()
        for path, body in bodies.items()
    }
    locs = "".join(f"<url><loc>{url}</loc></url>" for url in pages)
    pages[SITEMAP_URL] = (
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'.encode()
    )
    now = datetime(2026, 11, 23, tzinfo=UTC)
    fetch_corpus(tmp_path, get=pages.__getitem__, now=lambda: now, pause=lambda: None)
    return tmp_path


def test_page_becomes_a_document_with_one_line_per_block(tmp_path):
    [document] = load_documents(raw_dir_with(tmp_path)).documents
    assert document.id == "persoenliche_dokumente_und_bestaetigungen/reisepass/Seite.1"
    assert document.title == "Reisepass"
    assert document.text == "## Kosten\nDer Reisepass kostet 112 Euro.\n- Passfoto\nAlter | ab 12"
    assert document.metadata["last_updated"] == "2026-01-08"
    assert document.metadata["owner"] == "Bundeskanzleramt"


def test_link_lists_and_english_pages_are_left_out_and_counted(tmp_path):
    assert load_documents(raw_dir_with(tmp_path)).dropped == {"link list": 1, "english": 1}


def test_loader_rejects_a_raw_file_missing_from_the_manifest(tmp_path):
    raw_dir = raw_dir_with(tmp_path)
    (raw_dir / "pages" / "stray.html.gz").write_bytes(b"")
    with pytest.raises(ValueError, match="stray.html.gz"):
        load_documents(raw_dir)


def test_loader_rejects_a_raw_file_changed_since_the_fetch(tmp_path):
    raw_dir = raw_dir_with(tmp_path)
    first, second = read_manifest(raw_dir)[:2]
    (raw_dir / first.file).write_bytes((raw_dir / second.file).read_bytes())
    with pytest.raises(ValueError, match="changed since it was fetched"):
        load_documents(raw_dir)


def test_load_command_writes_one_line_per_document(tmp_path, capsys):
    out = tmp_path / "corpus" / "documents.jsonl"
    main(["load", "--raw-dir", str(raw_dir_with(tmp_path / "raw")), "--out", str(out)])
    assert len(out.read_text().splitlines()) == 1
    assert "Loaded 1 documents" in capsys.readouterr().out
