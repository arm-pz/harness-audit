"""inventory.py counts what an agent actually loads, including symlinked installs.

Run: python -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "harness-audit" / "scripts" / "inventory.py"


def inventory(root):
    out = subprocess.run([sys.executable, str(SCRIPT), str(root), "--no-user"],
                         capture_output=True, text=True, check=True, timeout=30)
    return json.loads(out.stdout)


class SymlinkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_skill_linked_by_npx_skills_add_is_counted(self):
        # npx skills add puts the skill in .agents/skills and links it into .claude/skills.
        self.write(".agents/skills/demo/SKILL.md", "---\nname: demo\n---\nbody\n")
        (self.root / ".claude/skills").mkdir(parents=True)
        os.symlink("../../.agents/skills/demo", self.root / ".claude/skills/demo")
        report = inventory(self.root)
        self.assertEqual(report["totals"]["skills"], 1)
        skill = report["skills"][0]
        self.assertEqual(skill["lines"], 4)
        self.assertEqual(os.path.realpath(skill["linked_to"]),
                         os.path.realpath(self.root / ".agents/skills/demo/SKILL.md"))

    def test_plain_skill_has_no_linked_to(self):
        self.write(".claude/skills/plain/SKILL.md", "---\nname: plain\n---\n")
        skill = inventory(self.root)["skills"][0]
        self.assertNotIn("linked_to", skill)

    def test_linked_rules_folder_is_read(self):
        self.write("shared/rules/a.md", "one rule\n")
        (self.root / ".claude").mkdir()
        os.symlink("../shared/rules", self.root / ".claude/rules")
        report = inventory(self.root)
        self.assertEqual(len(report["rules"]), 1)
        self.assertEqual(report["totals"]["rule_lines"], 1)

    def test_symlink_loop_is_visited_once(self):
        self.write(".claude/skills/demo/SKILL.md", "---\nname: demo\n---\n")
        os.symlink("..", self.root / ".claude/skills/demo/loop")
        self.assertEqual(inventory(self.root)["totals"]["skills"], 1)


if __name__ == "__main__":
    unittest.main()
