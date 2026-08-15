from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_FILE = ROOT / "simplify-report" / "SKILL.md"
INTERFACE_FILE = ROOT / "simplify-report" / "agents" / "openai.yaml"
CASES_FILE = Path(__file__).with_name("cases.json")


class SimplifyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_FILE.read_text(encoding="utf-8")
        cls.interface = INTERFACE_FILE.read_text(encoding="utf-8")
        cls.cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    def test_routing_catalog_has_distinct_positive_and_negative_prompts(self) -> None:
        routing = self.cases["routing"]
        positive = routing["should_trigger"]
        negative = routing["should_not_trigger"]

        self.assertGreaterEqual(len(positive), 4)
        self.assertGreaterEqual(len(negative), 4)
        self.assertFalse(set(positive) & set(negative))
        self.assertTrue(all(isinstance(prompt, str) and prompt.strip() for prompt in positive + negative))

    def test_execution_cases_are_complete_and_unique(self) -> None:
        cases = self.cases["execution"]
        names = [case["name"] for case in cases]

        self.assertGreaterEqual(len(cases), 6)
        self.assertEqual(len(names), len(set(names)))
        for case in cases:
            self.assertTrue(case["report"].strip())
            self.assertTrue(case["expected"])
            self.assertTrue(all(expectation.strip() for expectation in case["expected"]))

    def test_eval_contract_matches_skill_instructions(self) -> None:
        contract = "\n".join(self.cases["output_contract"])

        self.assertIn("**Bottom line.**", self.skill)
        self.assertIn("Use as many sentences as needed", self.skill)
        self.assertIn("Never omit a necessary explanation", self.skill)
        self.assertNotRegex(
            self.skill,
            re.compile(r"(?:one|1) to (?:three|3) sentences|no more than (?:three|3) sentences", re.IGNORECASE),
        )
        self.assertIn("Include every relevant question", self.skill)
        self.assertIn("verify that it matches the report", self.skill)
        self.assertRegex(contract, re.compile(r"no fixed sentence limit", re.IGNORECASE))
        self.assertRegex(contract, re.compile(r"does not omit a necessary explanation", re.IGNORECASE))
        self.assertRegex(contract, re.compile(r"severity.*uncertainty.*mixed outcomes", re.IGNORECASE))

    def test_default_prompt_invokes_the_skill(self) -> None:
        self.assertIn("$simplify-report", self.interface)


if __name__ == "__main__":
    unittest.main()
