from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "clean-up" / "SKILL.md"


class PowerShellDocumentationTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "PowerShell 5.1 transport is Windows-specific")
    def test_documented_validation_json_reaches_native_argv(self) -> None:
        skill_text = SKILL.read_text(encoding="utf-8")
        example = re.search(
            r"In Windows PowerShell 5\.1,.*?```text\s*"
            r"(?P<command>python --% scripts/apply_cleanup\.py[^\r\n]+)\s*```",
            skill_text,
            re.DOTALL,
        )
        self.assertIsNotNone(example, "PowerShell 5.1 example is missing")
        command = example.group("command")
        payload_match = re.search(r"--validate-command (?P<payload>\[[^\r\n]+\])$", command)
        self.assertIsNotNone(payload_match, "Documented validation payload is missing")
        payload = payload_match.group("payload")
        self.assertIn(r'\"python\"', payload)

        with tempfile.TemporaryDirectory() as temporary:
            echo_script = Path(temporary) / "argv_echo.py"
            echo_script.write_text(
                "import json, sys\nprint(json.dumps(sys.argv[1:]))\n",
                encoding="utf-8",
            )
            native_paths = (sys.executable, str(echo_script))
            if any(any(character.isspace() for character in path) for path in native_paths):
                self.skipTest("Native executable or fixture path contains whitespace")

            powershell_command = (
                f"{sys.executable} --% -B {echo_script} "
                f"--validation-command {payload}"
            )
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    powershell_command,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        received_arguments = json.loads(completed.stdout)
        self.assertEqual(received_arguments[0], "--validation-command")
        self.assertEqual(
            json.loads(received_arguments[1]),
            ["python", "-B", "-c", "print('ok')"],
        )


if __name__ == "__main__":
    unittest.main()
