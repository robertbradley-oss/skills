from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "clean-up"


class AsciiReportingTests(unittest.TestCase):
    def test_runtime_and_skill_reporting_sources_are_ascii_safe(self) -> None:
        paths = [PACKAGE / "SKILL.md", PACKAGE / "agents" / "openai.yaml"]
        paths.extend(sorted((PACKAGE / "scripts").glob("*.py")))

        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                data = path.read_bytes()
                try:
                    data.decode("ascii")
                except UnicodeDecodeError as exc:
                    self.fail(f"Non-ASCII reporting source {path}: byte {exc.start}")

    def test_skill_requires_plain_ascii_reports(self) -> None:
        text = (PACKAGE / "SKILL.md").read_text(encoding="ascii")
        self.assertIn("Use plain ASCII punctuation and symbols in every report", text)


if __name__ == "__main__":
    unittest.main()
