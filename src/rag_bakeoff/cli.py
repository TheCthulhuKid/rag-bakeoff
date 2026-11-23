"""Command line entry point: parses arguments, wires real dependencies, prints results."""

import argparse
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import httpx

from rag_bakeoff.corpus.fetch import fetch_corpus, read_manifest

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
    args = parser.parse_args(argv)
    _fetch(args.raw_dir, args.pause, transport)


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
