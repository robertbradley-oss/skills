import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "audit_definitions.py"
SPEC = importlib.util.spec_from_file_location("audit_definitions", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def agent(self, front="description: A useful task\ntools: [read, search]", body="Do the task."):
        return self.write("example.agent.md", f"---\n{front}\n---\n{body}\n")

    def codes(self):
        return {item["code"] for item in MODULE.audit(self.root)["findings"]}

    def test_valid_agent(self):
        self.agent()
        self.assertEqual(MODULE.audit(self.root)["errors"], 0)

    def test_duplicate_keys_rejected(self):
        self.agent("description: One\ndescription: Two")
        self.assertIn("yaml", self.codes())

    def test_missing_description_and_wrong_tools(self):
        self.agent("tools: 42")
        self.assertEqual(self.codes(), {"description", "tools"})

    def test_skill_name_must_match_directory(self):
        self.write("sample/SKILL.md", "---\nname: other\ndescription: Example\n---\nTask\n")
        self.assertIn("name", self.codes())

    def test_broken_link_with_line_number(self):
        self.agent(body="Read [guide](missing.md).")
        finding = MODULE.audit(self.root)["findings"][0]
        self.assertEqual((finding["code"], finding["line"]), ("broken-link", 5))

    def test_encoded_spaces_and_fragments(self):
        self.write("my guide.md", "# Guide")
        self.agent(body="[Guide](my%20guide.md#guide) [Anchor](#local) [Web](https://example.com)")
        self.assertEqual(self.codes(), set())

    def test_examples_are_not_link_targets(self):
        self.agent(body="```md\n[example](missing.md)\n```\n`[inline](missing.md)`")
        self.assertEqual(self.codes(), set())

    def test_unknown_host_field_is_warning(self):
        self.agent("description: Task\nfuture-property: true")
        report = MODULE.audit(self.root)
        self.assertEqual((report["errors"], report["warnings"]), (0, 1))

    def test_empty_directory_is_not_a_pass(self):
        self.assertEqual(self.codes(), {"empty"})

    def test_wrong_boolean_and_target(self):
        self.agent("description: Task\nuser-invocable: 'false'\ntarget: nowhere")
        self.assertEqual(self.codes(), {"user-invocable", "target"})

    def test_bad_yaml_and_non_mapping(self):
        self.agent("[not, a, mapping]")
        self.assertEqual(self.codes(), {"mapping"})
        self.agent("description: [broken")
        self.assertEqual(self.codes(), {"yaml"})

    def test_outside_root_link_is_not_read(self):
        self.agent(body="[Outside](../private.md)")
        self.assertEqual(self.codes(), {"outside-root"})

    def test_ignored_dependency_directory(self):
        self.agent()
        self.write("node_modules/fake/SKILL.md", "invalid")
        self.assertEqual(MODULE.audit(self.root)["files_checked"], 1)

    def test_oversized_or_empty_body(self):
        self.agent(body="x" * 30001)
        self.assertEqual(self.codes(), {"body-length"})
        self.agent(body="")
        self.assertEqual(self.codes(), {"body"})


if __name__ == "__main__":
    unittest.main()
