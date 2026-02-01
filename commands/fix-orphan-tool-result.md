---
description: Fix orphaned tool_result errors by removing tool_results without matching tool_use
argument-hint: <unique-text-from-conversation>
---

Fix the Claude Code API error caused by orphaned tool_result blocks in conversation history.

## Context

This error occurs when a conversation file contains a `tool_result` block that references a `tool_use_id` that doesn't exist in the conversation. This can happen due to streaming fallback errors, cancelled operations, or race conditions in Claude Code.

The API error looks like:
```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"messages.N.content.0: unexpected `tool_use_id` found in `tool_result` blocks: toolu_XXXXX. Each `tool_result` block must have a corresponding `tool_use` block in the previous message."}}
```

## Required Argument

**$ARGUMENTS** - A unique text string to identify the target conversation (e.g., the tool_use_id from the error, or a phrase from that session)

## Task

1. **Search for conversations** in `~/.claude/projects/` containing the search text: $ARGUMENTS
2. **Exclude the current conversation** (this one executing the command)
3. **If multiple matches remain**, automatically select the **most recently modified** file
4. **Analyze the selected conversation**:
   - Collect all `tool_use` ids from assistant messages
   - Collect all `tool_result` tool_use_ids from user messages
   - Identify orphaned tool_results (those with no matching tool_use)
5. **For each orphaned tool_result**:
   - Report the line number, tool_use_id, and content (often "Streaming fallback triggered")
   - Remove the entire JSONL line containing the orphaned tool_result
6. **Report results**:
   - Which file was selected (and why, if multiple matches)
   - Number of orphaned tool_results found and removed
   - Details of each orphan (line number, id, content snippet)
   - Backup location

## Implementation Notes

- Conversation files are JSONL format (one JSON object per line)
- tool_use blocks are in assistant messages: `line.message.content[]` where `content[].type === "tool_use"` with `content[].id`
- tool_result blocks are in user messages: `line.message.content[]` where `content[].type === "tool_result"` with `content[].tool_use_id`
- Use Python for JSON manipulation to preserve structure
- Remove entire lines containing orphaned tool_results (they are separate JSONL entries)
- Use file modification time (`os.path.getmtime()`) to determine latest file

## Safety

- Always create backup with `.bak` extension before modification
- Validate JSON after modification
- Report if backup already exists (append timestamp to avoid overwriting)
- If no orphans found, report that file is clean and exit gracefully
- If no matches found, report error and exit gracefully
