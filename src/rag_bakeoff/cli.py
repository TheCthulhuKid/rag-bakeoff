"""Command line entry point: parses arguments, wires real dependencies, prints results."""

import argparse
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import httpx

from rag_bakeoff.corpus.fetch import fetch_corpus, read_manifest
from rag_bakeoff.corpus.loader import load_documents, write_documents

USER_AGENT = "rag-bakeoff-corpus-fetch/0.1"


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
    load.add_argument("--out", type=Path, default=Path("data/corpus/documents.jsonl"))
    args = parser.parse_args(argv)
    if args.command == "fetch":
        _fetch(args.raw_dir, args.pause, transport)
    else:
        _load(args.raw_dir, args.out)


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
