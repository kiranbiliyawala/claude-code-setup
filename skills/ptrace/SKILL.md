---
name: ptrace
description: Analyze Playwright trace.zip files to debug E2E test failures. Use when investigating failed Playwright tests, extracting screenshots at error time, analyzing network requests, or correlating events around a timestamp.
---

# ptrace - Playwright Trace Inspector

CLI for extracting data from Playwright trace.zip files with JSON/JSONL output.

## Running

```bash
PYTHONPATH=~/.claude/skills python -m ptrace <trace.zip> <command> [options]
```

Run `--help` or `<command> --help` for all options.

## Debugging Workflow

When investigating a test failure:

```bash
# 1. Get overview
python -m ptrace trace.zip info --pretty

# 2. Find errors with context
python -m ptrace trace.zip errors --context --pretty

# 3. Extract screenshot at error
python -m ptrace trace.zip screenshot --error --out=error.jpeg

# 4. Correlate events around error timestamp if needed
python -m ptrace trace.zip correlate --at=<timestamp_ms> --window=1000
```

## Key Commands

| Command      | Purpose                                                  |
| ------------ | -------------------------------------------------------- |
| `info`       | Trace metadata and event counts                          |
| `errors`     | Test failures with `--context` for surrounding events    |
| `network`    | Requests with `--api-only`, `--status=4xx,5xx`, `--body` |
| `console`    | Logs with `--level=error`                                |
| `actions`    | Playwright actions with `--failed`                       |
| `screenshot` | Extract with `--error`, `--at=<ms>`, `--list`            |
| `correlate`  | Events in time window with `--at` and `--window`         |

## Output

Default is JSONL (one object per line). Use `--format=json` for array, `--pretty` for readability.
