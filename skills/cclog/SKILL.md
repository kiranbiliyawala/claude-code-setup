---
name: cclog
description: Agent-native CLI for reading and analyzing Claude Code JSONL conversation files. This skill should be used when searching Claude Code conversation logs, extracting tool calls, finding subagent sessions, viewing event timelines, or exporting conversations to other formats. Trigger phrases include "search my conversations", "find subagents", "show tool calls", "conversation timeline", "export log", or when analyzing .jsonl files from ~/.claude/projects/.
---

# cclog

Agent-native CLI for reading Claude Code JSONL conversation files.

## Usage

> **Skill location:** `~/.claude/skills/cclog`
>
> All commands below use `uv run` from the skill directory - no global installation required.

```bash
# Set shorthand (optional)
CCLOG=~/.claude/skills/cclog

# Run any command
cd $CCLOG && uv run cclog <command> [args]
```

**Alternative: Global install** (if you prefer `cclog` available everywhere):

```bash
cd ~/.claude/skills/cclog && uv pip install -e .
```

## Quick Reference

| Command     | Purpose                                |
| ----------- | -------------------------------------- |
| `info`      | Get file metadata (size, counts, time) |
| `messages`  | Extract messages with filtering        |
| `tools`     | Extract tool calls with results        |
| `search`    | Full-text search across content        |
| `subagents` | Find related subagent files            |
| `timeline`  | Event timeline with durations          |
| `export`    | Export to markdown, csv, llm format    |
| `batch`     | Process multiple files in parallel     |

## Common Usage Patterns

> **Note:** Examples below show `cclog` directly. When using `uv run`, prefix with `cd $CCLOG && uv run`:
> ```bash
> cd $CCLOG && uv run cclog info conversation.jsonl
> ```

### Get File Metadata

```bash
cclog info conversation.jsonl
cclog --format=human info conversation.jsonl
```

### Search Conversations

```bash
# Search for text in all content
cclog search conversation.jsonl "error"

# Search in specific content types
cclog search conversation.jsonl "validation" --in=tool_result

# Regex search with context
cclog search conversation.jsonl "\\d{3}" --regex --context=2
```

### Extract Tool Calls

```bash
# All tool calls
cclog tools conversation.jsonl

# Filter by tool name
cclog tools conversation.jsonl --name=Task

# Filter by subagent type
cclog tools conversation.jsonl --name=Task --subagent-type=general-purpose

# Only errors with full output
cclog tools conversation.jsonl --status=error --full
```

### Find Subagent Sessions

```bash
# List subagents from a file
cclog subagents conversation.jsonl

# Hierarchical tree view
cclog subagents conversation.jsonl --tree

# Find parent of subagent file
cclog subagents agent-a3f5885.jsonl --find-parent

# Find by session ID
cclog subagents --session=bba90b61-ff9e-4bf6-a3a8-43f13edf0c11
```

### Event Timeline

```bash
# Basic timeline
cclog timeline conversation.jsonl

# With durations between events
cclog timeline conversation.jsonl --show-duration

# Filter by event type and tool
cclog timeline conversation.jsonl --event-type=tool_use --tool=Task

# Summary statistics
cclog timeline conversation.jsonl --summary
```

### Export Conversations

```bash
# Export to markdown
cclog export conversation.jsonl --format=markdown

# Export to CSV
cclog export conversation.jsonl --format=csv -o tools.csv

# LLM-optimized export with token budget
cclog export conversation.jsonl --format=llm --max-tokens=25000

# JSON without thinking blocks
cclog export conversation.jsonl --format=simple-json --no-thinking
```

### Batch Operations

```bash
# Process all files in a project
cclog batch info --project=/path/to/project

# Search across multiple files
cclog batch search "error" --project=/path/to/project

# Extract tools with parallel processing
cclog batch tools --project=/path/to/project --workers=4
```

## Output Formats

Global `--format` option (before command):

| Format   | Description                     |
| -------- | ------------------------------- |
| `json`   | Formatted JSON (default)        |
| `human`  | Human-readable table via Rich   |
| `ndjson` | Newline-delimited JSON (stream) |

## Error Codes

| Code  | Type              | Description             |
| ----- | ----------------- | ----------------------- |
| E1001 | FILE_NOT_FOUND    | File does not exist     |
| E1002 | INVALID_JSONL     | Line is not valid JSON  |
| E1003 | NOT_CLAUDE_LOG    | Not a Claude Code log   |
| E1004 | EMPTY_FILE        | File is empty           |
| E2001 | FILTER_INVALID    | Invalid filter option   |
| E2002 | REGEX_INVALID     | Invalid regex pattern   |
| E3001 | SESSION_NOT_FOUND | Session files not found |
| E4001 | NO_FILES          | No files to process     |

## Exit Codes

| Code | Meaning         |
| ---- | --------------- |
| 0    | Success         |
| 1    | General error   |
| 2    | Invalid args    |
| 5    | Not found       |
| 8    | Partial success |
