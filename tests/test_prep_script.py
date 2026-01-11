import unittest
from pathlib import Path


class PrepScriptTests(unittest.TestCase):
    def test_prep_script_has_install_steps(self):
        script = Path(__file__).resolve().parents[1] / "prep.sh"
        content = script.read_text(encoding="utf-8")
        self.assertIn("install_pkg()", content)
        self.assertIn("apt-get", content)
        self.assertIn("ensure_python", content)
        self.assertIn("ensure_python_venv", content)
        self.assertIn("python3-venv", content)
        self.assertIn("ensure_cmd git", content)
        self.assertIn("ensure_cmd make", content)
        self.assertIn("VENV_PIP", content)
        self.assertIn("rm -rf", content)
        self.assertIn('chown -R "$USER":"$USER"', content)


if __name__ == "__main__":
    unittest.main()
