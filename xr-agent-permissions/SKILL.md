---
name: xr-agent-permissions
description: "Unified permission management for Claude Code, Gemini CLI, and Codex CLI. Use this skill whenever the user wants to manage, view, sync, add, or remove permission rules across AI coding agents. Trigger on: 管理 agent 权限, 同步权限配置, 添加/删除权限规则, 查看权限, /agent-permissions, or any mention of managing allow/deny/block rules for claude/gemini/codex CLI tools."
---

# Agent Permissions Manager

Unified permission management across three AI CLI tools:
- **Claude Code**: `~/.claude/settings.json`
- **Gemini CLI**: `~/.gemini/settings.json`
- **Codex CLI**: `~/.codex/config.toml`

## Format Differences

Each tool uses a different rule format. When converting a command (e.g., `git log`):

| Tool | Allow example | Deny example |
|------|--------------|--------------|
| Claude Code | `Bash(git log *)` | entry in `permissions.deny` |
| Gemini CLI | `git log` | entry in `sandbox.blockedCommands` |
| Codex CLI | `^git log( .*)?$` with `decision = "allow"` | same pattern with `decision = "forbidden"` |

Use `scripts/permissions.sh` for all reads and writes — never hand-edit the TOML/JSON directly without it, as TOML `[[shell_rules]]` arrays require careful handling.

## Workflow

### View current permissions

Run:
```bash
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh show
```

This prints a unified table of allow/deny rules across all three tools.

### Add a rule

Ask the user for:
1. The command pattern (e.g., `git log`, or a full regex/glob if they're specific)
2. The decision: `allow` or `deny`

Then run:
```bash
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh add --command "git log" --decision allow
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh add --command "curl" --decision deny
```

The script auto-converts the command into each tool's native format.

### Remove a rule

Ask the user which command to remove and from which decision list (allow/deny):
```bash
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh remove --command "git log" --decision allow
```

### Sync (overwrite all rules)

When the user provides a full list of allow/deny rules to replace the existing ones:
```bash
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh sync \
  --allow "git log" "git status" "npm run" \
  --deny "sudo" "rm -rf" "curl"
```

This replaces only the permission-managed entries in all three config files, leaving other settings untouched.

## Conversion Rules

When the user provides a plain command string, convert as follows:

**Claude Code** (`permissions.allow` / `permissions.deny`):
- Prefix with `Bash(` and append ` *)` for commands that take arguments
- Single-word commands with no typical args: `Bash(whoami)`, `Bash(pwd)`
- Example: `git log` → `Bash(git log *)`

**Gemini CLI** (`sandbox.allowedCommands` / `sandbox.blockedCommands`):
- Use the plain command string as-is (prefix match)
- Example: `git log` → `"git log"`

**Codex CLI** (`[[shell_rules]]` with `pattern` + `decision`):
- Wrap in `^...$` regex, append `( .*)?` to allow optional arguments
- Example: `git log` → `^git log( .*)?$`
- `allow` → `decision = "allow"`, `deny` → `decision = "forbidden"`

## After Changes

Always run `show` after making changes so the user can verify the result:
```bash
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh show
```
