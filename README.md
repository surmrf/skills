# xr-agent-permissions

Unified permission management for **Claude Code**, **Gemini CLI**, and **Codex CLI** — manage allow/deny rules across all three AI coding agents from a single place.

## Installation

```bash
npx skills add surmrf/xr-agent-permissions
```

## What it does

Each AI CLI tool stores permissions in different formats and locations:

| Tool | Config | Format |
|------|--------|--------|
| Claude Code | `~/.claude/settings.json` | `Bash(git log *)` glob style |
| Gemini CLI | `~/.gemini/settings.json` | `git log` plain prefix |
| Codex CLI | `~/.codex/config.toml` | `^git log( .*)?$` regex |

This skill provides a unified interface to manage them all at once, with automatic format conversion.

## Usage

Once installed, trigger the skill by saying:

- "管理 agent 权限"
- "查看三个工具的权限配置"
- "同步权限配置"
- "添加/删除权限规则"
- `/xr-agent-permissions`

### View current permissions

```bash
python ~/.agents/skills/xr-agent-permissions/scripts/permissions.py show
```

### Add a rule to all tools

```bash
python ~/.agents/skills/xr-agent-permissions/scripts/permissions.py add --command "git log" --decision allow
python ~/.agents/skills/xr-agent-permissions/scripts/permissions.py add --command "curl" --decision deny
```

### Remove a rule from all tools

```bash
python ~/.agents/skills/xr-agent-permissions/scripts/permissions.py remove --command "curl" --decision deny
```

### Sync (overwrite all rules)

```bash
python ~/.agents/skills/xr-agent-permissions/scripts/permissions.py sync \
  --allow "git log" "git status" "npm run" \
  --deny "sudo" "rm -rf" "curl"
```

## Requirements

- Python 3.8+
- One or more of: Claude Code, Gemini CLI, Codex CLI

## License

MIT
