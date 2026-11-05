#!/usr/bin/env python3
"""Mine Claude Code session transcripts for repeated corrections and tool use.

Usage: python mine_sessions.py <project-root> [--sessions-dir DIR] [--top N]

Reads ~/.claude/projects/<encoded-project-path>/*.jsonl by default.
Prints JSON: correction clusters (candidates only; a human or agent must
judge them) and tool-call counts by name. Examples are masked for
common secret shapes (API keys, tokens, JWTs, passwords, emails). Read-only. Standard library only.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

CUE = re.compile(
    r"^\s*(no\b|nope|don'?t|do not|stop|wrong|that'?s not|not what|"
    r"actually|instead|i said|i told you|again\b|why did you|you should(n'?t)?|"
    r"please don'?t|never\b|revert|undo)"
    r"|\b(i (already )?told you|as i said|you keep|every time|you forgot|"
    r"don'?t (ever )?(use|add|touch|change|run|create|delete))\b",
    re.I)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_\-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9\-]{10,}"
    r"|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"
    r"|(?i:(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*)\S+"
    r"|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")


def mask(text: str) -> str:
    return SECRET.sub("[masked]", text)


STOP = set("""masked a an the and or but if then else to of in on at for with by from is
are was were be been it this that these those i you we they he she me my your our
do does did not no don't dont just please can could would should will so as up
out about into over again actually instead stop wrong use using make made also
here there what why how when all any some its it's i'm im ok okay yes""".split())


def encode(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def user_text(record: dict):
    if record.get("type") != "user" or record.get("isMeta"):
        return None
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
            return None
        text = " ".join(c.get("text", "") for c in content
                        if isinstance(c, dict) and c.get("type") == "text")
    else:
        return None
    text = text.strip()
    if not text or text.startswith("<") or len(text) > 2000:
        return None  # command wrappers, system injections, pasted dumps
    return text


def tokens(text: str) -> set:
    text = re.sub(r"[’']", "", text.lower())  # don't -> dont (a stopword)
    out = set()
    for w in re.findall(r"[a-z_][a-z0-9_.\-/]*[a-z0-9_]", text):
        parts = [w] + [p for p in re.split(r"[.\-/]", w) if p] if re.search(r"[.\-/]", w) else [w]
        out.update(p for p in parts if len(p) > 2 and p not in STOP)
    return out


def cluster(items, threshold=0.3):
    groups = []
    for item in items:
        best, best_score = None, 0.0
        for g in groups:
            union = item["tokens"] | g["tokens"]
            score = len(item["tokens"] & g["tokens"]) / len(union) if union else 0
            if score > best_score:
                best, best_score = g, score
        if best and best_score >= threshold:
            best["members"].append(item)
            best["terms"].update(item["tokens"])
        else:
            groups.append({"tokens": set(item["tokens"]), "members": [item],
                           "terms": Counter(item["tokens"])})
    for g in groups:  # terms seen in more than one member, most common first
        shared = [t for t, n in g["terms"].most_common() if n > 1]
        g["shared"] = shared or [t for t, _ in g["terms"].most_common(5)]
    return groups


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    root = Path(argv[0]).resolve()
    sessions_dir = Path.home() / ".claude" / "projects" / encode(root)
    top = 15
    if "--sessions-dir" in argv:
        sessions_dir = Path(argv[argv.index("--sessions-dir") + 1]).expanduser()
    if "--top" in argv:
        top = int(argv[argv.index("--top") + 1])

    files = sorted(sessions_dir.glob("*.jsonl")) if sessions_dir.is_dir() else []
    result = {"sessions_dir": str(sessions_dir), "sessions": len(files),
              "user_messages": 0, "correction_candidates": 0,
              "clusters": [], "tool_calls": {}}
    if not files:
        result["note"] = "no session transcripts found; correction mining skipped"
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    candidates, tools = [], Counter()
    for f in files:
        with f.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("type") == "assistant":
                    for c in (rec.get("message") or {}).get("content") or []:
                        if isinstance(c, dict) and c.get("type") == "tool_use":
                            tools[c.get("name", "?")] += 1
                    continue
                text = user_text(rec)
                if text is None:
                    continue
                result["user_messages"] += 1
                clean = mask(text)
                if CUE.search(text) and tokens(clean):
                    candidates.append({"session": f.stem, "text": clean[:300],
                                       "tokens": tokens(clean)})

    result["correction_candidates"] = len(candidates)
    groups = cluster(candidates)
    ranked = []
    for g in groups:
        sessions = {m["session"] for m in g["members"]}
        ranked.append({
            "count": len(g["members"]),
            "sessions": len(sessions),
            "shared_terms": g["shared"][:12],
            "examples": [m["text"] for m in g["members"][:4]],
            "repeated": len(g["members"]) >= 3 and len(sessions) >= 2,
        })
    ranked.sort(key=lambda r: (r["repeated"], r["count"], r["sessions"]), reverse=True)
    result["clusters"] = ranked[:top]
    result["tool_calls"] = dict(tools.most_common())
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
