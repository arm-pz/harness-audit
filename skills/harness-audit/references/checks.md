# The six checks

Each check has a pass condition, what counts as evidence, and the fix to propose. A check passes when it produces no finding above `trial-remove`.

## 1. Missed corrections → `add-rule` or `enforce`

Source: `sessions.json` clusters.

- A cluster with **3+ corrections across 2+ sessions** is a missing rule.
- If the correction is mechanical (formatting, a forbidden command, a file that must not be touched, tests not run), propose a hook or linter rule, not prose.
- If it is judgement (naming, architecture preference), propose one line in the right instruction file, worded as the instruction plus its reason.
- If it is a whole area the agent keeps getting wrong (env vars, auth, migrations) and needs more than a line, use `action: handoff` to `portable-harness` for a map section.
- Check first that no existing rule already covers it. If one does and the correction still recurs, that rule is being ignored → move it to check 5.

## 2. Unproven rules → `trial-remove` or `delete`

Source: instruction files + `sessions.json`.

- `delete`: the rule duplicates another rule, contradicts another rule, refers to a file, command, library or tool that no longer exists, or restates default model behaviour ("write clean code", "be careful").
- `trial-remove`: no correction in the mined sessions relates to it and it is not a hard constraint (security, data loss, compliance). Propose removing it for a set period and re-running the audit.
- Keep, and list under "Kept on purpose", any rule guarding against an irreversible action even without session evidence.

## 3. Instruction file size → `merge` or move

Source: `inventory.json` line counts.

- Main instruction file (CLAUDE.md or AGENTS.md at the root) over **~100 lines** is a finding. Over 200 is high impact.
- The fix is to keep the main file as a map: project purpose, commands, where things live, and pointers to topic files (`docs/`, `.claude/rules/`) loaded only when relevant.
- Flag nested instruction files that repeat the root file.

## 4. Tool and skill load → `remove-tool`

Source: `inventory.json` MCP servers and skills, `sessions.json` tool counts.

- An MCP server whose tools were never called in the mined sessions is a candidate for removal or for loading only in the projects that use it.
- Two tools or skills that do the same job: propose keeping the one used more.
- A skill whose description overlaps another's: hand off to `tune-skill` rather than rewriting it here.
- If fewer than ~10 sessions were mined, downgrade every `remove-tool` to `trial-remove`; the sample is too small.

## 5. Prose with no enforcement → `enforce`

Source: instruction files + `inventory.json` hooks, plus the repo's lint, test and pre-commit config.

- Any rule using MUST, NEVER, ALWAYS, or about security, secrets, formatting, tests, file boundaries or commands is a candidate.
- If nothing executable checks it (hook, linter rule, CI step, pre-commit, test), propose the smallest script that does. Prefer extending existing tooling over a new hook.
- If the check needed is a new-errors-only type check, opt-in live-service tests or a deploy gate, use `action: handoff` to `portable-harness`, which owns those three recipes.
- Once enforced, propose shortening the prose rule to one line pointing at the check.

## 6. Drift → `delete` or update

Source: instruction files vs the repo.

- Paths, scripts, commands, env vars, package names and folder structures named in instruction files must exist. Verify with the filesystem or package manifest; do not guess.
- Each stale reference is a finding with the corrected line as its diff.
- Recommend a recurring re-audit if drift findings exceed three.

## Scoring

One point per check with no finding at `delete`, `enforce`, `add-rule`, `merge` or `remove-tool` level. `trial-remove` findings do not cost a point; a `handoff` finding costs the point of the check that raised it. Report the score as x/6 and never round up.
