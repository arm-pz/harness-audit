# harness-audit

An agent skill that audits and prunes the harness you already have: CLAUDE.md / AGENTS.md, rules files, hooks, MCP servers and skills. It reads your past Claude Code sessions to find corrections you keep repeating, checks which rules and tools earn their place, and returns a ranked report with diffs. Nothing changes until you pick which findings to apply.

The best harnesses are small, evidence-based and constantly pruned. This skill does the pruning.

Install: `npx skills add arm-pz/harness-audit --skill harness-audit`

Ask it things like:

- "My CLAUDE.md is 400 lines now, help me cut it down."
- "Which of my MCP servers am I actually using?"
- "Claude keeps making the same mistakes and I can't tell which rule is missing."
- "Feels like the agent got dumber since I added all those rules."

## What you get

| Check | What it flags | Typical fix |
|---|---|---|
| Missed corrections | The same correction 3+ times across 2+ sessions with no rule for it | One-line rule, or a hook if it's mechanical |
| Unproven rules | Duplicates, contradictions, rules about things that no longer exist, rules restating default behaviour | Delete, or trial-remove and re-audit |
| File size | A main instruction file over ~100 lines | Keep it as a map that points to topic files |
| Tool load | MCP servers never called, skills that do the same job | Remove, or load only where used |
| Unenforced prose | MUST/NEVER rules nothing checks | The smallest hook, lint rule or test that does |
| Drift | Paths, commands and packages named in docs that don't exist | Corrected line |

The report ends with a score out of 6, what was kept on purpose, and what wasn't checked.

Two scripts do the deterministic work: `inventory.py` lists the harness, and `mine_sessions.py` clusters correction-style messages and counts tool calls from `~/.claude/projects/`. Secrets in session text (API keys, tokens, JWTs, passwords, emails) are masked before anything is printed. Both use the Python standard library only.

## Not for

Writing a new setup, rules, map sections or guardrails for a named problem area (`portable-harness`, which this skill hands findings to in a fixed block), reviewing application code (`consistent-code-review`), or fixing a skill's trigger description (`tune-skill`).

## Install

```
npx skills add arm-pz/harness-audit --skill harness-audit
```

Or copy `skills/harness-audit/` into your agent's skills directory (`.claude/skills/`, `.agents/skills/`, `.cursor/skills/` or `.qoder/skills/`). With Claude Code plugins, `.claude-plugin/plugin.json` makes the repo installable as a plugin.

## Structure

```
harness-audit/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── harness-audit/
│       ├── SKILL.md
│       ├── references/
│       │   └── checks.md         # thresholds, evidence and fix per check
│       └── scripts/
│           ├── inventory.py
│           └── mine_sessions.py
└── tests/
    ├── evals.json
    └── test-cases.md
```

## Credits

The six practices come from u/Marmelab's r/ClaudeAI post "How to build a harness that actually improves your agent", a review of 57 publications on coding-agent harnesses.

## Test results

Version 0.1.0: script tests pass on fixture repos and sessions (inventory totals, repeated-correction clustering, skip on missing sessions, secret masking); 10 trigger cases judged by hand from the descriptions, not run in a live agent.

## Known limits

Correction detection works on wording ("no, don't…", "actually…", "you forgot…"), so it misses corrections phrased as plain new instructions and can catch ordinary messages that start the same way. The agent reads each cluster before calling it a finding. The scripts haven't yet been run on real transcripts, Windows paths, or user-level config, so check one run on your machine first.
