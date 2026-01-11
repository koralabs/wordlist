#!/usr/bin/env python3
import argparse
import sys
import datetime
import urllib.request
from pathlib import Path

from make_wordlist import count_token_length, iter_wordlist_file

HANDLES_URL = "https://api.handle.me/handles"
DEFAULT_CACHE_PATH = Path(".cache/handles.txt")


def fetch_handles_text(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"Accept": "text/plain"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def get_handles_text(
    url: str,
    timeout: int,
    cache_path: Path,
    fetcher=fetch_handles_text,
    prompt=input,
) -> str:
    if cache_path.exists():
        mtime = datetime.datetime.fromtimestamp(cache_path.stat().st_mtime)
        ts = mtime.strftime("%Y-%m-%d %H:%M:%S")
        answer = prompt(
            f"Cached Handles list found at {cache_path} (modified {ts}). "
            "Use cache? [Y/n] "
        ).strip().lower()
        if answer in {"", "y", "yes"}:
            return cache_path.read_text(encoding="utf-8", errors="ignore")

    text = fetcher(url, timeout)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")
    return text


def parse_wordlist_text(text: str) -> set[str]:
    words = set()
    for line in text.splitlines():
        token = line.strip()
        if token:
            words.add(token.lower())
    return words


def load_english_words(path, max_len: int) -> set[str]:
    path = Path(path)
    words = set()
    for word in iter_wordlist_file(path):
        token = word.strip()
        if not token:
            continue
        if count_token_length(token) > max_len:
            continue
        words.add(token.lower())
    return words


def sorted_by_length(words: set[str]) -> list[str]:
    return sorted(words, key=lambda w: (len(w), w))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Find English words not present in the Handles list."
    )
    parser.add_argument(
        "--wordlist",
        default="wordlist.txt",
        help="Path to wordlist.txt (one word per line).",
    )
    parser.add_argument(
        "--out",
        default="unminted_handles.txt",
        help="Output path for Handles not yet minted.",
    )
    parser.add_argument(
        "--url",
        default=HANDLES_URL,
        help="Handles API endpoint (text/plain).",
    )
    parser.add_argument(
        "--cache-path",
        type=Path,
        default=DEFAULT_CACHE_PATH,
        help="Cache file path (default: .cache/handles.txt).",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=15,
        help="Max length allowed (punctuation counts).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Network timeout in seconds.",
    )
    args = parser.parse_args(argv)

    english = load_english_words(args.wordlist, args.max_len)
    handles_text = get_handles_text(args.url, args.timeout, args.cache_path)
    handles = parse_wordlist_text(handles_text)
    missing = sorted_by_length(english - handles)

    out_path = Path(args.out)
    out_path.write_text("\n".join(missing) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
