#!/usr/bin/env python3
from __future__ import annotations
"""Unified permission manager for Claude Code, Gemini CLI, and Codex CLI."""

import argparse
import json
import re
import sys
from pathlib import Path

CLAUDE_SETTINGS = Path.home() / ".claude/settings.json"
GEMINI_SETTINGS = Path.home() / ".gemini/settings.json"
CODEX_CONFIG = Path.home() / ".codex/config.toml"


# ── Format converters ──────────────────────────────────────────────────────────

NO_ARGS_CMDS = {"env", "pwd", "whoami", "date", "pip list", "go version", "cargo --version", "rustc --version"}

def to_claude(cmd: str) -> str:
    """git log  →  Bash(git log *)"""
    return f"Bash({cmd})" if cmd in NO_ARGS_CMDS else f"Bash({cmd} *)"

def to_gemini(cmd: str) -> str:
    """git log  →  git log  (plain prefix)"""
    return cmd

def to_codex_pattern(cmd: str) -> str:
    """git log  →  ^git log( .*)?$"""
    escaped = re.escape(cmd)
    return f"^{escaped}( .*)?$"

def from_claude(entry: str) -> str | None:
    """Bash(git log *)  →  git log"""
    m = re.match(r"^Bash\((.+?)( \*)?\)$", entry)
    return m.group(1) if m else None

def from_gemini(entry: str) -> str:
    return entry

def from_codex_pattern(pattern: str) -> str | None:
    """^git log( .*)?$  →  git log"""
    m = re.match(r"^\^(.+?)(\( \.\*\)\?)?\\?\$$", pattern)
    if not m:
        m = re.match(r"^\^(.+?)(\( \.\*\)\?)?\$$", pattern)
    if m:
        return re.sub(r"\\(.)", r"\1", m.group(1))
    return None


# ── JSON helpers ───────────────────────────────────────────────────────────────

def read_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ── TOML helpers (stdlib-only, handles [[shell_rules]]) ───────────────────────

def read_toml_raw(path: Path) -> str:
    return path.read_text() if path.exists() else ""

def parse_shell_rules(text: str) -> list[dict]:
    rules = []
    for block in re.finditer(r"\[\[shell_rules\]\]\s*\n(.*?)(?=\[\[|\Z)", text, re.DOTALL):
        rule = {}
        for line in block.group(1).splitlines():
            m = re.match(r'\s*(\w+)\s*=\s*"([^"]*)"', line)
            if m:
                rule[m.group(1)] = m.group(2)
        if rule:
            rules.append(rule)
    return rules

def remove_shell_rules_section(text: str) -> str:
    return re.sub(r"\[\[shell_rules\]\]\s*\n(?:.*\n)*?(?=\[\[|\Z)", "", text).rstrip()

def render_shell_rules(rules: list[dict]) -> str:
    lines = []
    for rule in rules:
        lines.append('\n[[shell_rules]]')
        lines.append(f'pattern = "{rule["pattern"]}"')
        lines.append(f'decision = "{rule["decision"]}"')
    return "\n".join(lines)

def write_toml_with_rules(path: Path, rules: list[dict]) -> None:
    raw = read_toml_raw(path)
    base = remove_shell_rules_section(raw)
    new_text = base + render_shell_rules(rules) + "\n"
    path.write_text(new_text)


# ── Read current state ─────────────────────────────────────────────────────────

def get_claude_rules() -> tuple[list[str], list[str]]:
    data = read_json(CLAUDE_SETTINGS)
    perms = data.get("permissions", {})
    return perms.get("allow", []), perms.get("deny", [])

def get_gemini_rules() -> tuple[list[str], list[str]]:
    data = read_json(GEMINI_SETTINGS)
    sb = data.get("sandbox", {})
    return sb.get("allowedCommands", []), sb.get("blockedCommands", [])

def get_codex_rules() -> tuple[list[str], list[str]]:
    rules = parse_shell_rules(read_toml_raw(CODEX_CONFIG))
    allow = [r["pattern"] for r in rules if r.get("decision") == "allow"]
    deny = [r["pattern"] for r in rules if r.get("decision") == "forbidden"]
    return allow, deny


# ── Show ───────────────────────────────────────────────────────────────────────

def cmd_show(_args) -> None:
    c_allow, c_deny = get_claude_rules()
    g_allow, g_deny = get_gemini_rules()
    x_allow, x_deny = get_codex_rules()

    print("╔══════════════════════════════════════════════════════╗")
    print("║              Agent Permissions Overview              ║")
    print("╠══════════════════════════════════════════════════════╣")

    def section(title, allow, deny):
        print(f"\n  ┌─ {title}")
        if allow:
            print(f"  │  ✅ ALLOW ({len(allow)})")
            for e in allow:
                print(f"  │     {e}")
        if deny:
            print(f"  │  ❌ DENY ({len(deny)})")
            for e in deny:
                print(f"  │     {e}")
        if not allow and not deny:
            print("  │     (empty)")

    section("Claude Code  (~/.claude/settings.json)", c_allow, c_deny)
    section("Gemini CLI   (~/.gemini/settings.json)", g_allow, g_deny)
    section("Codex CLI    (~/.codex/config.toml)", x_allow, x_deny)
    print()


# ── Add ────────────────────────────────────────────────────────────────────────

def cmd_add(args) -> None:
    cmd = args.command
    decision = args.decision  # "allow" or "deny"

    # Claude Code
    data = read_json(CLAUDE_SETTINGS)
    data.setdefault("permissions", {})
    key = "allow" if decision == "allow" else "deny"
    entries = data["permissions"].setdefault(key, [])
    entry = to_claude(cmd)
    if entry not in entries:
        entries.append(entry)
        write_json(CLAUDE_SETTINGS, data)
        print(f"[claude]  +{decision}: {entry}")

    # Gemini CLI
    data = read_json(GEMINI_SETTINGS)
    data.setdefault("sandbox", {})
    g_key = "allowedCommands" if decision == "allow" else "blockedCommands"
    g_entries = data["sandbox"].setdefault(g_key, [])
    g_entry = to_gemini(cmd)
    if g_entry not in g_entries:
        g_entries.append(g_entry)
        write_json(GEMINI_SETTINGS, data)
        print(f"[gemini]  +{decision}: {g_entry}")

    # Codex CLI
    rules = parse_shell_rules(read_toml_raw(CODEX_CONFIG))
    pattern = to_codex_pattern(cmd)
    x_decision = "allow" if decision == "allow" else "forbidden"
    # Check exact match OR if the command is already covered by an existing pattern
    already_covered = any(
        r["pattern"] == pattern or
        (r.get("decision") == x_decision and re.fullmatch(r["pattern"], cmd))
        for r in rules
    )
    if not already_covered:
        rules.append({"pattern": pattern, "decision": x_decision})
        write_toml_with_rules(CODEX_CONFIG, rules)
        print(f"[codex]   +{decision}: {pattern}")
    else:
        print(f"[codex]   already covered: {cmd}")

    print("Done.")


# ── Remove ─────────────────────────────────────────────────────────────────────

def cmd_remove(args) -> None:
    cmd = args.command
    decision = args.decision

    # Claude Code
    data = read_json(CLAUDE_SETTINGS)
    key = "allow" if decision == "allow" else "deny"
    entries = data.get("permissions", {}).get(key, [])
    target = to_claude(cmd)
    if target in entries:
        entries.remove(target)
        write_json(CLAUDE_SETTINGS, data)
        print(f"[claude]  -{decision}: {target}")

    # Gemini CLI
    data = read_json(GEMINI_SETTINGS)
    g_key = "allowedCommands" if decision == "allow" else "blockedCommands"
    g_entries = data.get("sandbox", {}).get(g_key, [])
    g_entry = to_gemini(cmd)
    if g_entry in g_entries:
        g_entries.remove(g_entry)
        write_json(GEMINI_SETTINGS, data)
        print(f"[gemini]  -{decision}: {g_entry}")

    # Codex CLI
    rules = parse_shell_rules(read_toml_raw(CODEX_CONFIG))
    pattern = to_codex_pattern(cmd)
    before = len(rules)
    rules = [r for r in rules if not (r["pattern"] == pattern)]
    if len(rules) < before:
        write_toml_with_rules(CODEX_CONFIG, rules)
        print(f"[codex]   -{decision}: {pattern}")

    print("Done.")


# ── Sync ───────────────────────────────────────────────────────────────────────

def cmd_sync(args) -> None:
    allow_cmds: list[str] = args.allow or []
    deny_cmds: list[str] = args.deny or []

    # Claude Code
    data = read_json(CLAUDE_SETTINGS)
    data.setdefault("permissions", {})
    data["permissions"]["allow"] = [to_claude(c) for c in allow_cmds]
    data["permissions"]["deny"] = [to_claude(c) for c in deny_cmds]
    write_json(CLAUDE_SETTINGS, data)
    print(f"[claude]  synced ({len(allow_cmds)} allow, {len(deny_cmds)} deny)")

    # Gemini CLI
    data = read_json(GEMINI_SETTINGS)
    data.setdefault("sandbox", {})
    data["sandbox"]["allowedCommands"] = [to_gemini(c) for c in allow_cmds]
    data["sandbox"]["blockedCommands"] = [to_gemini(c) for c in deny_cmds]
    write_json(GEMINI_SETTINGS, data)
    print(f"[gemini]  synced ({len(allow_cmds)} allow, {len(deny_cmds)} deny)")

    # Codex CLI
    rules = [{"pattern": to_codex_pattern(c), "decision": "allow"} for c in allow_cmds]
    rules += [{"pattern": to_codex_pattern(c), "decision": "forbidden"} for c in deny_cmds]
    write_toml_with_rules(CODEX_CONFIG, rules)
    print(f"[codex]   synced ({len(allow_cmds)} allow, {len(deny_cmds)} deny)")

    print("Done.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified agent permission manager")
    sub = parser.add_subparsers(dest="command_name", required=True)

    sub.add_parser("show", help="Show current permissions across all tools")

    p_add = sub.add_parser("add", help="Add a rule to all tools")
    p_add.add_argument("--command", required=True, help="Command string, e.g. 'git log'")
    p_add.add_argument("--decision", required=True, choices=["allow", "deny"])

    p_rm = sub.add_parser("remove", help="Remove a rule from all tools")
    p_rm.add_argument("--command", required=True)
    p_rm.add_argument("--decision", required=True, choices=["allow", "deny"])

    p_sync = sub.add_parser("sync", help="Overwrite all rules in all tools")
    p_sync.add_argument("--allow", nargs="*", default=[], metavar="CMD")
    p_sync.add_argument("--deny", nargs="*", default=[], metavar="CMD")

    args = parser.parse_args()
    {"show": cmd_show, "add": cmd_add, "remove": cmd_remove, "sync": cmd_sync}[args.command_name](args)


if __name__ == "__main__":
    main()
