---
description: Fix compaction errors by removing thinking blocks from conversation files
argument-hint: <unique-text-from-conversation>
---

Fix the Claude Code compaction error caused by thinking blocks in conversation history.

## Context

The compaction error occurs when Claude Code tries to summarize a conversation containing `thinking` or `redacted_thinking` blocks. The API rejects modifications to these blocks, causing a 400 error:

```
Error during compaction: Error: API Error: 400
"thinking" or "redacted_thinking" blocks in the latest assistant message cannot be modified
```

## Required Argument

**$ARGUMENTS** - A unique text string to identify the target conversation (e.g., a phrase from that session)

## Task

1. **Search for conversations** in `~/.claude/projects/` containing the search text: $ARGUMENTS
2. **Exclude the current conversation** (this one executing the command)
3. **If multiple matches remain**, automatically select the **most recently modified** file
4. **For the selected conversation**:
   - Create a backup with `.backup` extension
   - Remove all `thinking` and `redacted_thinking` content blocks from assistant messages
   - Preserve all other content (text, tool_use, tool_result blocks)
   - Validate the resulting JSON is valid
5. **Report results**:
   - Which file was selected (and why, if multiple matches)
   - Number of thinking blocks removed
   - Backup location

## Implementation Notes

- Conversation files are JSONL format (one JSON object per line)
- Thinking blocks are in: `line.message.content[]` where `content[].type === "thinking"` or `"redacted_thinking"`
- Only modify lines where `line.type === "assistant"`
- Use Python for JSON manipulation to preserve structure
- Use file modification time (`os.path.getmtime()`) to determine latest file

## Safety

- Always create backup before modification
- Validate JSON after modification
- Report if backup already exists (don't overwrite previous backups)
- If no matches found, report error and exit gracefully
