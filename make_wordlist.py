#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TOKEN_RE = re.compile(r"^[A-Za-z]+(?:-[A-Za-z]+)*$")
DEFAULT_SCOWL_DIR = Path(__file__).resolve().parent / "sources" / "scowl"
DEFAULT_SCOWL_SIZE = 70
DEFAULT_SCOWL_CLASS = "A"
DEFAULT_SCOWL_VARIANT = "5"


def iter_wordlist_file(path: Path):
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            word = line.strip()
            if word:
                yield word


def iter_wiktextract_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("lang") != "English":
                continue
            word = obj.get("word")
            if isinstance(word, str) and word:
                yield word


def iter_wordfreq_words(wordlist_name: str):
    try:
        from wordfreq import iter_wordlist
    except ImportError:
        raise RuntimeError("wordfreq is not installed. Try: pip install wordfreq")
    for word in iter_wordlist("en", wordlist=wordlist_name):
        yield word


def count_token_length(token: str) -> int:
    return len(token)


def normalize_token(token: str) -> str:
    return token.strip().lower().replace("'", "")


def collect_source(words):
    source = set()
    for word in words:
        token = normalize_token(word)
        if token:
            source.add(token)
    return source


def merge_sources(sources, intersection: bool):
    if not sources:
        return set()
    if intersection:
        merged = set(sources[0])
        for source in sources[1:]:
            merged &= source
        return merged
    merged = set()
    for source in sources:
        merged |= source
    return merged


def filter_words(words, max_len: int):
    kept = set()
    for word in words:
        token = normalize_token(word)
        if not token:
            continue
        if not TOKEN_RE.match(token):
            continue
        if count_token_length(token) > max_len:
            continue
        kept.add(token.lower())
    return sorted(kept)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Merge word sources and filter by length."
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=15,
        help="Max length (punctuation counts toward length).",
    )
    parser.add_argument(
        "--no-intersection",
        action="store_true",
        help="Disable intersection mode (use union instead).",
    )
    parser.add_argument(
        "--scowl-size",
        type=int,
        default=DEFAULT_SCOWL_SIZE,
        help="SCOWL size parameter (larger is broader).",
    )
    parser.add_argument(
        "--scowl-no-filter",
        action="store_true",
        help="Disable SCOWL's default word filter (adds --no-word-filter).",
    )
    parser.add_argument(
        "--wordlist",
        type=Path,
        action="append",
        default=[],
        help="Path to a newline-delimited word list. Repeatable.",
    )
    parser.add_argument(
        "--wiktextract-jsonl",
        type=Path,
        help="Path to wiktextract JSONL output (English entries).",
    )
    parser.add_argument(
        "--wordfreq-disabled",
        action="store_true",
        help="Disable wordfreq list (enabled by default).",
    )
    parser.add_argument(
        "--wordfreq-list",
        default="best",
        choices=["small", "best", "large"],
        help="wordfreq list name.",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default="wordlist.txt",
        help="Output path for the merged word list.",
    )
    return parser.parse_args(argv)


def format_subprocess_error(exc: subprocess.CalledProcessError) -> str:
    message = f"Command {exc.cmd!r} failed with exit code {exc.returncode}."
    stdout = getattr(exc, "stdout", None)
    if stdout is None:
        stdout = getattr(exc, "output", None)
    stderr = getattr(exc, "stderr", None)
    output = "\n".join([stdout or "", stderr or ""]).strip()
    if output:
        message = f"{message}\n{output}"
    return message


def ensure_scowl_db(scowl_dir: Path, runner=subprocess.run) -> Path:
    db_path = scowl_dir / "scowl.db"
    if not db_path.exists():
        try:
            runner(
                ["make", "scowl.db"],
                cwd=scowl_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(format_subprocess_error(exc)) from exc
    return db_path


def scowl_wordlist(
    scowl_dir: Path,
    size: int,
    no_filter: bool,
    runner=subprocess.run,
) -> list[str]:
    scowl_path = scowl_dir / "scowl"
    if not scowl_path.exists():
        raise RuntimeError(f"scowl script not found at {scowl_path}")
    db_path = ensure_scowl_db(scowl_dir, runner=runner)
    args = ["word-list", str(size), DEFAULT_SCOWL_CLASS, DEFAULT_SCOWL_VARIANT]
    if no_filter:
        args.append("--no-word-filter")
    result = runner(
        [str(scowl_path), "--db", str(db_path), *args],
        cwd=scowl_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def main(argv) -> int:
    args = parse_args(argv)
    sources = []

    try:
        sources.append(
            collect_source(
                scowl_wordlist(
                    DEFAULT_SCOWL_DIR, args.scowl_size, args.scowl_no_filter
                )
            )
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.wordlist:
        wordlist_words = set()
        for path in args.wordlist:
            wordlist_words.update(collect_source(iter_wordlist_file(path)))
        sources.append(wordlist_words)

    if args.wiktextract_jsonl:
        sources.append(
            collect_source(iter_wiktextract_jsonl(args.wiktextract_jsonl))
        )

    if not args.wordfreq_disabled:
        try:
            sources.append(collect_source(iter_wordfreq_words(args.wordfreq_list)))
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    words = merge_sources(sources, not args.no_intersection)
    filtered = filter_words(words, args.max_len)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(filtered) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
