"""Command line entry point: parses arguments, wires real dependencies, prints results."""

import argparse
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import httpx

from rag_bakeoff.corpus.fetch import fetch_corpus, read_manifest
from rag_bakeoff.corpus.loader import load_documents, read_documents, write_documents
from rag_bakeoff.corpus.questions import QuestionFileError, load_questions

USER_AGENT = "rag-bakeoff-corpus-fetch/0.1"
DOCUMENTS = Path("data/corpus/documents.jsonl")


def main(
    argv: Sequence[str] | None = None, *, transport: httpx.BaseTransport | None = None
) -> None:
    """Run the command line. `transport` replaces the network, for tests."""
    parser = argparse.ArgumentParser(prog="rag-bakeoff")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download the corpus pages that are not stored yet")
    fetch.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    fetch.add_argument("--pause", type=float, default=1.0, help="seconds between page requests")
    load = commands.add_parser("load", help="turn the fetched pages into the documents file")
    load.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    load.add_argument("--out", type=Path, default=DOCUMENTS)
    check = commands.add_parser("check-questions", help="validate a golden question file")
    check.add_argument("path", type=Path, nargs="?", default=Path("questions/golden-v1.jsonl"))
    check.add_argument("--documents", type=Path, default=DOCUMENTS)
    fetch.set_defaults(run=lambda args: _fetch(args.raw_dir, args.pause, transport))
    load.set_defaults(run=lambda args: _load(args.raw_dir, args.out))
    check.set_defaults(run=lambda args: _check_questions(args.path, args.documents))
    args = parser.parse_args(argv)
    args.run(args)


def _fetch(raw_dir: Path, pause_seconds: float, transport: httpx.BaseTransport | None) -> None:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(
        headers=headers, timeout=30, follow_redirects=True, transport=transport
    ) as client:

        def get(url: str) -> bytes:
            return client.get(url).raise_for_status().content

        fetched = fetch_corpus(
            raw_dir,
            get=get,
            now=lambda: datetime.now(UTC),
            pause=lambda: time.sleep(pause_seconds),
        )
    print(f"Fetched {len(fetched)} new pages, {len(read_manifest(raw_dir))} in {raw_dir} in total.")


def _load(raw_dir: Path, out: Path) -> None:
    result = load_documents(raw_dir)
    write_documents(result.documents, out)
    left_out = ", ".join(f"{count} {reason}" for reason, count in sorted(result.dropped.items()))
    print(f"Loaded {len(result.documents)} documents into {out}. Left out: {left_out or 'none'}.")


def _check_questions(path: Path, documents: Path) -> None:
    try:
        questions = load_questions(path, read_documents(documents))
    except QuestionFileError as error:
        print(f"{len(error.problems)} problems in {path}:")
        print("\n".join(f"  {problem}" for problem in error.problems))
        raise SystemExit(1) from error
    unanswerable = sum(not question.answerable for question in questions)
    multi_document = sum(len(question.expected_document_ids) > 1 for question in questions)
    print(
        f"{len(questions)} questions are valid: {len(questions) - unanswerable} answerable "
        f"({multi_document} with several documents), {unanswerable} unanswerable."
    )
