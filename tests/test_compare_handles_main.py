import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import compare_handles


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        return False


class CompareHandlesMainTests(unittest.TestCase):
    def test_fetch_handles_text_uses_plain_text_accept_header(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["accept"] = request.get_header("Accept")
            captured["timeout"] = timeout
            return FakeResponse(b"alpha\nbeta\n")

        with patch.object(compare_handles.urllib.request, "urlopen", side_effect=opener):
            text = compare_handles.fetch_handles_text("https://example.com/handles", 12)

        self.assertEqual(text, "alpha\nbeta\n")
        self.assertEqual(captured["url"], "https://example.com/handles")
        self.assertEqual(captured["accept"], "text/plain")
        self.assertEqual(captured["timeout"], 12)

    def test_get_handles_text_fetches_when_cache_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "handles.txt"

            def fetcher(url, timeout):
                self.assertEqual(url, "https://example.com")
                self.assertEqual(timeout, 5)
                return "fresh\n"

            text = compare_handles.get_handles_text(
                "https://example.com",
                5,
                cache_path,
                fetcher=fetcher,
                prompt=lambda _msg: "y",
            )

            self.assertEqual(text, "fresh\n")
            self.assertEqual(cache_path.read_text(encoding="utf-8"), "fresh\n")

    def test_main_writes_sorted_unminted_handles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wordlist_path = Path(tmpdir) / "wordlist.txt"
            output_path = Path(tmpdir) / "missing.txt"
            cache_path = Path(tmpdir) / "cache.txt"

            wordlist_path.write_text("banana\napple\ncarrot\n", encoding="utf-8")

            with patch.object(compare_handles, "get_handles_text", return_value="apple\n"), patch.object(
                compare_handles, "HANDLES_URL", "https://example.com"
            ):
                result = compare_handles.main(
                    [
                        "--wordlist",
                        str(wordlist_path),
                        "--out",
                        str(output_path),
                        "--cache-path",
                        str(cache_path),
                        "--max-len",
                        "10",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8").splitlines(), ["banana", "carrot"])


if __name__ == "__main__":
    unittest.main()
