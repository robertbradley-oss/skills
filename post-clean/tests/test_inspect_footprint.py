from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "post-clean" / "scripts" / "inspect_footprint.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class InspectFootprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / ".gameplan" / "footprints").mkdir(parents=True)
        (self.workspace / "tmp").mkdir()
        (self.workspace / "tmp" / "debug.log").write_text("debug\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def copy_fixture(self, name: str, target: str = "source.md") -> str:
        destination = self.workspace / ".gameplan" / "footprints" / target
        shutil.copyfile(FIXTURES / name, destination)
        return destination.relative_to(self.workspace).as_posix()

    def inspect(self, footprint: str | None = None) -> dict:
        command = [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--workspace",
            str(self.workspace),
            "--format",
            "json",
        ]
        if footprint:
            command.extend(["--footprint", footprint])
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        return json.loads(completed.stdout)

    def test_finalized_source_emits_stable_state_bound_candidate(self) -> None:
        footprint = self.copy_fixture("finalized.md")
        (self.workspace / "src").mkdir()
        (self.workspace / "src" / "keep.txt").write_text("keep\n", encoding="utf-8")

        first = self.inspect(footprint)
        second = self.inspect(footprint)

        self.assertFalse(first["mutations_performed"])
        self.assertTrue(first["apply_supported"])
        self.assertEqual(first["provisional_authorization_set"], second["provisional_authorization_set"])
        self.assertEqual(len(first["provisional_authorization_set"]), 1)
        candidate = next(item for item in first["items"] if item["classification"] == "candidate")
        self.assertEqual(candidate["path"], "tmp/debug.log")
        self.assertRegex(candidate["id"], r"^PC-[A-F0-9]{12}$")
        kept = next(item for item in first["items"] if item["path"] == "src/keep.txt")
        self.assertEqual(kept["classification"], "preserve")
        self.assertEqual((self.workspace / "tmp" / "debug.log").read_text(), "debug\n")

        (self.workspace / "tmp" / "debug.log").write_text("changed\n", encoding="utf-8")
        changed = self.inspect(footprint)
        self.assertNotEqual(
            first["provisional_authorization_set"], changed["provisional_authorization_set"]
        )

    def test_active_source_preserves_and_refuses_authorization(self) -> None:
        footprint = self.copy_fixture("active.md")
        result = self.inspect(footprint)

        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertIn("source-not-finalized", {item["code"] for item in result["refusals"]})
        self.assertTrue(all(item["classification"] == "preserve" for item in result["items"]))

    def test_unknown_schema_preserves_and_refuses_authorization(self) -> None:
        footprint = self.copy_fixture("unknown-schema.md")
        result = self.inspect(footprint)

        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertIn("unsupported-schema", {item["code"] for item in result["refusals"]})
        self.assertTrue(all(item["classification"] == "preserve" for item in result["items"]))

    def test_ambiguous_gameplan_selection_has_no_candidates(self) -> None:
        shutil.copyfile(FIXTURES / "ambiguous-gameplan.md", self.workspace / "GAMEPLAN.md")
        result = self.inspect()

        self.assertEqual(result["source"]["selection"], "ambiguous")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["provisional_authorization_set"], [])
        self.assertIn("source-ambiguous", {item["code"] for item in result["refusals"]})

    def test_gameplan_selects_materialized_compiled_v1_footprint(self) -> None:
        relative = ".gameplan/footprints/compiled.md"
        compiled = self.workspace / Path(relative)
        compiled.write_text(
            """# GamePlan Compiled Footprint

Schema: `gameplan-task-footprint/v1`
Task: `Compiled provenance`
Plan: `GAMEPLAN.md`
State: `finalized`
Started: `2026-07-19`
Finalized: `2026-07-19`
Baseline: `Materialized from explicitly ordered finalized sources`
Coverage: `workspace paths only`
Scope: `compiled`

## Compiled sources

| Order | Footprint |
|---|---|
| `1` | `.gameplan/footprints/task-one.md` |
| `2` | `.gameplan/footprints/task-two.md` |

## Protected pre-existing items

| Path | Observed state | Protection reason |
|---|---|---|

## Task items

| Path | Origin | Kind | Disposition | Intent |
|---|---|---|---|---|
| `tmp/debug.log` | `created` | `temporary` | `remove` | Compiled cleanup candidate. |

## Cleanup obligations

| Path | Action | Status | Reason |
|---|---|---|---|
| `tmp/debug.log` | `remove` | `open` | Remove compiled residue. |
""",
            encoding="utf-8",
        )
        (self.workspace / "GAMEPLAN.md").write_text(
            f"# Game Plan\n\n## Task Footprint\n\nFinalized: `{relative}`\n",
            encoding="utf-8",
        )

        result = self.inspect()

        self.assertEqual(result["source"]["selection"], "gameplan")
        self.assertEqual(result["source"]["path"], relative)
        self.assertEqual(result["source"]["schema"], "gameplan-task-footprint/v1")
        self.assertEqual(result["source"]["state"], "finalized")
        self.assertEqual(len(result["provisional_authorization_set"]), 1)
        candidate = next(item for item in result["items"] if item["classification"] == "candidate")
        self.assertEqual(candidate["path"], "tmp/debug.log")


if __name__ == "__main__":
    unittest.main()
