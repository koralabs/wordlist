import tempfile
import unittest
from pathlib import Path

from compare_handles import (
    get_handles_text,
    load_english_words,
    parse_wordlist_text,
    sorted_by_length,
)


class CompareHandlesTests(unittest.TestCase):
    def test_parse_wordlist_text_lowercases(self):
        text = "Hello\nworld\n\nHELLO\n"
        words = parse_wordlist_text(text)
        self.assertEqual(words, {"hello", "world"})

    def test_sorted_by_length(self):
        words = {"bbb", "a", "cc"}
        self.assertEqual(sorted_by_length(words), ["a", "cc", "bbb"])

    def test_load_english_words_filters_by_letter_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "english.txt"
            path.write_text("re-do\nabcde\n", encoding="utf-8")
            words = load_english_words(path, max_len=5)
            self.assertEqual(words, {"re-do", "abcde"})

    def test_get_handles_text_uses_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "handles.txt"
            cache_path.write_text("cached\n", encoding="utf-8")

            def fetcher(url, timeout):
                raise AssertionError("fetcher should not be called")

            text = get_handles_text(
                "https://example.com",
                1,
                cache_path,
                fetcher=fetcher,
                prompt=lambda _: "y",
            )
            self.assertEqual(text, "cached\n")

    def test_get_handles_text_refreshes_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "handles.txt"
            cache_path.write_text("cached\n", encoding="utf-8")

            def fetcher(url, timeout):
                return "fresh\n"

            text = get_handles_text(
                "https://example.com",
                1,
                cache_path,
                fetcher=fetcher,
                prompt=lambda _: "n",
            )
            self.assertEqual(text, "fresh\n")
            self.assertEqual(
                cache_path.read_text(encoding="utf-8", errors="ignore"),
                "fresh\n",
            )


if __name__ == "__main__":
    unittest.main()
