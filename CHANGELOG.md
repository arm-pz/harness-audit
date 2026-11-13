# Changelog

## 0.1.1 (2026-11-13)
- inventory.py follows symlinked folders, so skills installed with `npx skills add` (linked from `.agents/skills/`) are counted instead of reading 0; linked files carry `linked_to`. Symlink loops are visited once. Found by the skill's own real run on arm-pz/caffeinity-skills.
- A check with nothing to examine (check 1 under 2 sessions, no rules, no instruction files, no references) is INCONCLUSIVE and earns no point; the score shows how many were inconclusive.
- SKILL.md says which hook sources the inventory does not read.
- Tests: tests/test_inventory.py covers a linked skill, a linked rules folder and a symlink loop.

## 0.1.0 (2026-11-05)
- Initial release from u/Marmelab's six harness practices: inventory and session-mining scripts, six checks with scoring, report plus approval-gated diffs; 10 test cases.
- Tuned against portable-harness: harness-audit judges and removes, portable-harness writes setup; findings needing new setup go over in a HARNESS-AUDIT HANDOFF block.
- Session examples and cluster terms are masked for common secret shapes.
- Tests: script tests pass on fixtures; 10 trigger cases reviewed-only.
