import builtins
import json
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import make_wordlist


class MakeWordlistMainTests(unittest.TestCase):
    def test_parse_args_maps_flags(self):
        args = make_wordlist.parse_args(
            [
                "--max-len",
                "12",
                "--no-intersection",
                "--scowl-size",
                "60",
                "--scowl-no-filter",
                "--wordlist",
                "extra.txt",
                "--wiktextract-jsonl",
                "wiktextract.jsonl",
                "--wordfreq-disabled",
                "--out",
                "out.txt",
            ]
        )

        self.assertEqual(args.max_len, 12)
        self.assertTrue(args.no_intersection)
        self.assertEqual(args.scowl_size, 60)
        self.assertTrue(args.scowl_no_filter)
        self.assertEqual(args.wordlist, [Path("extra.txt")])
        self.assertEqual(args.wiktextract_jsonl, Path("wiktextract.jsonl"))
        self.assertTrue(args.wordfreq_disabled)
        self.assertEqual(args.out, Path("out.txt"))

    def test_iter_wordfreq_words_success(self):
        fake_module = types.SimpleNamespace(iter_wordlist=lambda *_args, **_kwargs: ["alpha", "beta"])
        with patch.dict("sys.modules", {"wordfreq": fake_module}):
            self.assertEqual(list(make_wordlist.iter_wordfreq_words("best")), ["alpha", "beta"])

    def test_iter_wordfreq_words_import_error(self):
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "wordfreq":
                raise ImportError("missing")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded_import):
            with self.assertRaises(RuntimeError) as ctx:
                list(make_wordlist.iter_wordfreq_words("best"))
        self.assertIn("wordfreq is not installed", str(ctx.exception))

    def test_format_subprocess_error_includes_output(self):
        exc = subprocess.CalledProcessError(2, ["cmd"], "stdout-data", "stderr-data")
        message = make_wordlist.format_subprocess_error(exc)
        self.assertIn("exit code 2", message)
        self.assertIn("stdout-data", message)
        self.assertIn("stderr-data", message)

    def test_ensure_scowl_db_uses_existing_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scowl_dir = Path(tmpdir)
            db_path = scowl_dir / "scowl.db"
            db_path.write_text("", encoding="utf-8")

            result = make_wordlist.ensure_scowl_db(scowl_dir)
            self.assertEqual(result, db_path)

    def test_ensure_scowl_db_wraps_make_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scowl_dir = Path(tmpdir)

            def runner(*_args, **_kwargs):
                raise subprocess.CalledProcessError(2, ["make", "scowl.db"], "out", "err")

            with self.assertRaises(RuntimeError) as ctx:
                make_wordlist.ensure_scowl_db(scowl_dir, runner=runner)
            message = str(ctx.exception)
            self.assertIn("out", message)
            self.assertIn("err", message)

    def test_scowl_wordlist_requires_scowl_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError) as ctx:
                make_wordlist.scowl_wordlist(Path(tmpdir), 70, False)
            self.assertIn("scowl script not found", str(ctx.exception))

    def test_main_success_writes_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wordlist_path = Path(tmpdir) / "extra.txt"
            wiktextract_path = Path(tmpdir) / "wiktextract.jsonl"
            output_path = Path(tmpdir) / "wordlist.txt"

            wordlist_path.write_text("Alpha\nbeta\n", encoding="utf-8")
            wiktextract_path.write_text(
                "\n".join(
                    [
                        json.dumps({"lang": "English", "word": "Gamma"}),
                        json.dumps({"lang": "French", "word": "bonjour"}),
                    ]
                ),
                encoding="utf-8",
            )

            with patch.object(make_wordlist, "scowl_wordlist", return_value=["delta", "alpha"]):
                result = make_wordlist.main(
                    [
                        "--wordfreq-disabled",
                        "--no-intersection",
                        "--wordlist",
                        str(wordlist_path),
                        "--wiktextract-jsonl",
                        str(wiktextract_path),
                        "--max-len",
                        "10",
                        "--out",
                        str(output_path),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8").splitlines(), ["alpha", "beta", "delta", "gamma"])

    def test_main_returns_2_when_scowl_fails(self):
        with patch.object(make_wordlist, "scowl_wordlist", side_effect=RuntimeError("scowl failed")):
            result = make_wordlist.main(["--wordfreq-disabled"])
        self.assertEqual(result, 2)

    def test_main_returns_2_when_wordfreq_fails(self):
        with patch.object(make_wordlist, "scowl_wordlist", return_value=["alpha"]), patch.object(
            make_wordlist, "iter_wordfreq_words", side_effect=RuntimeError("wordfreq failed")
        ):
            result = make_wordlist.main([])
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
