#!/usr/bin/env python3
"""List an agent harness in a project and print it as JSON.

Usage: python inventory.py <project-root> [--no-user]

Finds instruction files, .claude/ rules, settings, hooks, MCP servers,
skills, commands and agents, in the project and (unless --no-user) in
~/.claude. Read-only. Standard library only.
"""
import json
import sys
from pathlib import Path

INSTRUCTION_NAMES = {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "GEMINI.md",
                     ".cursorrules", ".windsurfrules", "copilot-instructions.md"}
SKIP_DIRS = {".git", "node_modules", "bin", "obj", "dist", "build", ".venv",
             "venv", "__pycache__", ".next", "target", "vendor"}


def line_count(path: Path) -> int:
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
    except OSError:
        return -1


def walk(root: Path, max_depth: int = 6):
    stack = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in SKIP_DIRS and depth < max_depth:
                    stack.append((entry, depth + 1))
            else:
                yield entry


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def hooks_from(settings: dict, source: str):
    out = []
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups or []:
            for hook in group.get("hooks", []) or []:
                out.append({"source": source, "event": event,
                            "matcher": group.get("matcher", ""),
                            "command": hook.get("command", "")})
    return out


def mcp_from(config: dict, source: str):
    servers = (config or {}).get("mcpServers") or {}
    return [{"source": source, "name": name,
             "command": (spec or {}).get("command") or (spec or {}).get("url", "")}
            for name, spec in servers.items()]


def scan_claude_dir(base: Path, label: str, report: dict, root: Path):
    if not base.is_dir():
        return
    for name in ("settings.json", "settings.local.json"):
        path = base / name
        data = load_json(path)
        if data is not None:
            report["settings"].append(str(path))
            report["hooks"].extend(hooks_from(data, f"{label}:{name}"))
            report["mcp_servers"].extend(mcp_from(data, f"{label}:{name}"))
            perms = data.get("permissions") or {}
            for key in ("allow", "deny", "ask"):
                if perms.get(key):
                    report["permissions"][f"{label}:{key}"] = len(perms[key])
    for kind in ("rules", "commands", "agents"):
        folder = base / kind
        if folder.is_dir():
            for f in sorted(folder.rglob("*.md")):
                report[kind].append({"path": str(f), "lines": line_count(f)})
    skills = base / "skills"
    if skills.is_dir():
        for f in sorted(skills.rglob("SKILL.md")):
            report["skills"].append({"path": str(f), "lines": line_count(f)})


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0]).resolve()
    include_user = "--no-user" not in sys.argv

    report = {"project": str(root), "instruction_files": [], "settings": [],
              "hooks": [], "mcp_servers": [], "permissions": {}, "rules": [],
              "commands": [], "agents": [], "skills": [], "lint_and_ci": []}

    for f in walk(root):
        if f.name in INSTRUCTION_NAMES:
            report["instruction_files"].append(
                {"path": str(f.relative_to(root)), "lines": line_count(f)})
        elif f.name in {".pre-commit-config.yaml", ".editorconfig", ".eslintrc",
                        ".eslintrc.json", "eslint.config.js", "ruff.toml",
                        ".golangci.yml", "Directory.Build.props", ".husky"} \
                or ".github/workflows" in str(f).replace("\\", "/"):
            report["lint_and_ci"].append(str(f.relative_to(root)))

    mcp = load_json(root / ".mcp.json")
    if mcp is not None:
        report["mcp_servers"].extend(mcp_from(mcp, "project:.mcp.json"))
    scan_claude_dir(root / ".claude", "project", report, root)

    if include_user:
        home = Path.home()
        user_md = home / ".claude" / "CLAUDE.md"
        if user_md.is_file():
            report["instruction_files"].append(
                {"path": str(user_md), "lines": line_count(user_md)})
        scan_claude_dir(home / ".claude", "user", report, root)
        user_cfg = load_json(home / ".claude.json")
        if user_cfg is not None:
            report["mcp_servers"].extend(mcp_from(user_cfg, "user:.claude.json"))
            proj = (user_cfg.get("projects") or {}).get(str(root)) or {}
            report["mcp_servers"].extend(mcp_from(proj, "user:.claude.json(project)"))

    report["instruction_files"].sort(key=lambda x: -x["lines"])
    report["totals"] = {
        "instruction_lines": sum(max(f["lines"], 0) for f in report["instruction_files"]),
        "rule_lines": sum(max(f["lines"], 0) for f in report["rules"]),
        "hooks": len(report["hooks"]),
        "mcp_servers": len(report["mcp_servers"]),
        "skills": len(report["skills"]),
    }
    json.dump(report, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
