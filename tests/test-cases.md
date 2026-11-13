# Trigger test cases

Judged by hand from the descriptions of harness-audit, portable-harness, consistent-code-review and tune-skill (not run in a live agent).

| # | Message | Expected skill | Pass condition | Hand result |
| --- | --- | --- | --- | --- |
| 1 | "My CLAUDE.md is 400 lines now, help me cut it down" | harness-audit | report flags check 3; nothing edited before approval | pass |
| 2 | "Which of my MCP servers am I actually using?" | harness-audit | lists servers with call counts from sessions | pass |
| 3 | "Audit my agent setup in this repo" | harness-audit | report has a Score x/6 and a "Not checked" section | pass |
| 4 | "Claude keeps making the same mistakes and I can't tell which rule is missing" | harness-audit | mines sessions before proposing any rule | pass (close to portable-harness's "keeps ignoring conventions") |
| 5 | "Feels like the agent got dumber since I added all those rules" | harness-audit | runs inventory before giving any opinion | pass |
| 6 | "Set up agent rules for this repo" | portable-harness | harness-audit does not trigger | pass |
| 7 | "My CLAUDE.md is 900 lines and Claude still gets env vars wrong" | portable-harness | harness-audit does not trigger (named area) | pass, closest call: "too long" matches both; the "named problem area" Not-for decides it |
| 8 | "Review this PR for bugs" | consistent-code-review | harness-audit does not trigger | pass |
| 9 | "My recruiter-lens skill fires on the wrong requests" | tune-skill | harness-audit does not trigger | pass |
| 10 | "Audit my site's SEO" | searchfit-seo:seo-audit | shares "audit"; harness-audit does not trigger | pass |

## Boundary pairs

| Message | Should trigger | Why |
| --- | --- | --- |
| "My CLAUDE.md is a mess, what should go?" | harness-audit | existing setup, judge and remove |
| "Write me a CLAUDE.md for this project" | portable-harness | nothing to audit, writes setup |
| "Which of my rules actually do anything?" | harness-audit | verdict on existing rules |
| "Claude keeps hitting the real Stripe API in tests" | portable-harness | named area with a ready guardrail recipe |
| Spanning: "Clean up my harness, then add the guardrails it's missing" | harness-audit → portable-harness | audit first; `action: handoff` findings go over in the HARNESS-AUDIT HANDOFF block |

## Script tests (run)

- `inventory.py` on a fixture repo (140-line CLAUDE.md, 1 hook, 3 MCP servers, 1 rules file): totals correct.
- `mine_sessions.py` on 4 fixture sessions: a correction repeated 3× across 3 sessions is marked `repeated`; a 2× one is not; tool counts correct; a missing sessions folder returns a skip note with exit 0.
- `inventory.py` symlinks (`tests/test_inventory.py`, 4 cases): a skill linked from `.agents/skills/` the way `npx skills add` installs it counts as 1 with `linked_to`; a plain skill has no `linked_to`; a symlinked rules folder is read; a symlink loop is visited once. The linked-skill case fails on 0.1.0 and passes on 0.1.1.

## Scoring case (reviewed-only)

- A repo with no instruction files, no rules, one mined session and one `handoff` finding under check 4: the report scores 0/6 (5 inconclusive), not 5/6, and lists checks 1, 2, 3, 5 and 6 under "Not checked" with their reasons. This is the arm-pz/caffeinity-skills run of 2026-11-13, which reported 5/6 under 0.1.0.

- Secret masking: API key, GitHub token and email in correction text appear as `[masked]` in both examples and shared terms; zero raw secrets in output.
