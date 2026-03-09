# skills

A collection of agent skills for Claude Code, Gemini CLI, and Codex CLI.

## xr-agent-permissions

Unified permission management for **Claude Code**, **Gemini CLI**, and **Codex CLI** — manage allow/deny rules across all three AI coding agents from a single place, with automatic format conversion.

### Installation

```bash
npx skills add https://github.com/surmrf/skills --skill xr-agent-permissions
```

### What it does

Each AI CLI tool stores permissions in a different format:

| Tool | Config | Format |
|------|--------|--------|
| Claude Code | `~/.claude/settings.json` | `Bash(git log *)` glob style |
| Gemini CLI | `~/.gemini/settings.json` | `git log` plain prefix |
| Codex CLI | `~/.codex/config.toml` | `^git log( .*)?$` regex |

This skill manages them all at once and handles format conversion automatically.

### Usage

Trigger the skill by saying:

- "管理 agent 权限"
- "查看三个工具的权限配置"
- "同步权限配置"
- "添加/删除权限规则"
- `/xr-agent-permissions`

Or use the script directly:

```bash
# View current permissions across all tools
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh show

# Add a rule to all tools
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh add --command "git log" --decision allow

# Remove a rule from all tools
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh remove --command "curl" --decision deny

# Sync (overwrite all rules at once)
sh ~/.agents/skills/xr-agent-permissions/scripts/permissions.sh sync \
  --allow "git log" "git status" "npm run" \
  --deny "sudo" "rm -rf" "curl"
```

### Update

```bash
npx skills update xr-agent-permissions
```

### Requirements

- Python 3.8+ or Python 2.7+
- One or more of: Claude Code, Gemini CLI, Codex CLI

## License

MIT
