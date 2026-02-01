# cclog

Agent-native CLI for reading Claude Code JSONL conversation files.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Get file metadata
cclog info conversation.jsonl

# Human-readable output
cclog info conversation.jsonl --format=human

# Extract messages with filtering
cclog messages conversation.jsonl --role=assistant --limit=10
cclog messages conversation.jsonl --content-type=tool_use --tool=Task

# Extract tool calls with results
cclog tools conversation.jsonl --name=Task
cclog tools conversation.jsonl --name=Task --subagent-type=general-purpose
cclog tools conversation.jsonl --status=error --full

# Full-text search
cclog search conversation.jsonl "error" --in=tool_result
cclog search conversation.jsonl "validation" --context=2
cclog search conversation.jsonl "\\d{3}" --regex -i

# Find subagent sessions
cclog subagents conversation.jsonl
cclog subagents conversation.jsonl --tree
cclog subagents agent-a3f5885.jsonl --find-parent
cclog subagents --session=bba90b61-ff9e-4bf6-a3a8-43f13edf0c11

# Event timeline
cclog timeline conversation.jsonl
cclog timeline conversation.jsonl --show-duration
cclog timeline conversation.jsonl --event-type=tool_use --tool=Task
cclog timeline conversation.jsonl --group-by=tool
cclog timeline conversation.jsonl --summary

# Export to various formats
cclog export conversation.jsonl --format=markdown
cclog export conversation.jsonl --format=csv -o tools.csv
cclog export conversation.jsonl --format=llm --max-tokens=25000
cclog export conversation.jsonl --format=simple-json --no-thinking

# Batch operations (parallel processing)
cclog batch info --project=/path/to/project
cclog batch info --files='["file1.jsonl", "file2.jsonl"]'
cclog batch search "error" --project=/path/to/project
cclog batch tools --project=/path/to/project --fail-fast
cclog batch timeline --project=/path/to/project --summary

# Show capabilities
cclog capabilities
```

## Commands

| Command     | Status      | Description                        |
| ----------- | ----------- | ---------------------------------- |
| `info`      | Implemented | Get file metadata                  |
| `messages`  | Implemented | Extract messages with filtering    |
| `tools`     | Implemented | Extract tool calls with results    |
| `search`    | Implemented | Full-text search                   |
| `subagents` | Implemented | Find related subagent files        |
| `timeline`  | Implemented | Event timeline with durations      |
| `export`    | Implemented | Export to markdown, csv, llm       |
| `batch`     | Implemented | Process multiple files in parallel |

## Error Codes

| Code  | Type                | Description                        |
| ----- | ------------------- | ---------------------------------- |
| E1001 | FILE_NOT_FOUND      | File does not exist                |
| E1002 | INVALID_JSONL       | Line is not valid JSON             |
| E1003 | NOT_CLAUDE_LOG      | Not a Claude Code conversation log |
| E1004 | EMPTY_FILE          | File is empty                      |
| E1005 | PROJECT_NOT_FOUND   | Project directory not found        |
| E2001 | FILTER_INVALID      | Invalid filter option              |
| E2002 | REGEX_INVALID       | Invalid regex pattern              |
| E2003 | TIMESTAMP_PARSE_ERR | Cannot parse timestamp             |
| E3001 | SESSION_NOT_FOUND   | Session files not found            |
| E4001 | NO_FILES            | No files to process                |
| E4002 | INVALID_COMMAND     | Unknown batch command              |

## Exit Codes

| Code | Meaning         |
| ---- | --------------- |
| 0    | Success         |
| 1    | General error   |
| 2    | Invalid args    |
| 5    | Not found       |
| 8    | Partial success |
