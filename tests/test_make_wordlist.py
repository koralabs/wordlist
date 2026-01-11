import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from make_wordlist import (
    collect_source,
    count_token_length,
    filter_words,
    iter_wiktextract_jsonl,
    iter_wordlist_file,
    merge_sources,
    normalize_token,
    scowl_wordlist,
)


class WordlistTests(unittest.TestCase):
    def test_count_token_length_includes_punct(self):
        self.assertEqual(count_token_length("re-do"), 5)
        self.assertEqual(count_token_length("cant"), 4)

    def test_normalize_token_removes_apostrophes(self):
        self.assertEqual(normalize_token("Can't"), "cant")

    def test_collect_source_normalizes(self):
        words = collect_source(["Hello", "can't", ""])
        self.assertEqual(words, {"hello", "cant"})

    def test_filter_words_rules(self):
        words = {
            "Hello",
            "hello",
            "re-do",
            "can't",
            "cant",
            "toolong-word-here",
            "rock-",
            "hello!",
            "state-of-the",
        }
        result = filter_words(words, max_len=10)
        self.assertIn("hello", result)
        self.assertIn("re-do", result)
        self.assertIn("cant", result)
        self.assertNotIn("can't", result)
        self.assertNotIn("state-of-the", result)
        self.assertNotIn("toolong-word-here", result)
        self.assertNotIn("rock-", result)
        self.assertNotIn("hello!", result)

    def test_merge_sources_union(self):
        merged = merge_sources([{"a", "b"}, {"b", "c"}], intersection=False)
        self.assertEqual(merged, {"a", "b", "c"})

    def test_merge_sources_intersection(self):
        merged = merge_sources([{"a", "b"}, {"b", "c"}], intersection=True)
        self.assertEqual(merged, {"b"})

    def test_iter_wordlist_file_skips_blank(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "list.txt"
            path.write_text("alpha\n\nbeta\n", encoding="utf-8")
            words = list(iter_wordlist_file(path))
            self.assertEqual(words, ["alpha", "beta"])

    def test_iter_wiktextract_jsonl_filters_lang(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dump.jsonl"
            lines = [
                {"lang": "English", "word": "cool"},
                {"lang": "French", "word": "cool"},
                "not json",
            ]
            content = "\n".join(
                [json.dumps(lines[0]), json.dumps(lines[1]), lines[2]]
            )
            path.write_text(content, encoding="utf-8")
            words = list(iter_wiktextract_jsonl(path))
            self.assertEqual(words, ["cool"])

    def test_scowl_wordlist_runs_make_for_missing_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scowl_dir = Path(tmpdir)
            (scowl_dir / "scowl").write_text("", encoding="utf-8")
            calls = []

            def runner(cmd, cwd, check, capture_output, text):
                calls.append(cmd)
                if cmd[0] == "make":
                    (Path(cwd) / "scowl.db").write_text("", encoding="utf-8")
                    return SimpleNamespace(stdout="")
                return SimpleNamespace(stdout="alpha\nbeta\n")

            words = scowl_wordlist(scowl_dir, 60, True, runner=runner)
            self.assertEqual(words, ["alpha", "beta"])
            self.assertEqual(calls[0], ["make", "scowl.db"])
            self.assertIn("60", calls[1])
            self.assertIn("--no-word-filter", calls[1])

    def test_scowl_wordlist_reports_make_failure_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scowl_dir = Path(tmpdir)
            (scowl_dir / "scowl").write_text("", encoding="utf-8")

            def runner(cmd, cwd, check, capture_output, text):
                if cmd[0] == "make":
                    raise subprocess.CalledProcessError(
                        2, cmd, "make out", "make err"
                    )
                return SimpleNamespace(stdout="")

            with self.assertRaises(RuntimeError) as ctx:
                scowl_wordlist(scowl_dir, 60, False, runner=runner)
            message = str(ctx.exception)
            self.assertIn("make out", message)
            self.assertIn("make err", message)


if __name__ == "__main__":
    unittest.main()
