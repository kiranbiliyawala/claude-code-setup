---
name: skill-reviewer
description: >-
  Reviews Claude Code skills for design quality using per-file agents. Supports
  three modes: PR review, full skill audit, and issue validation. This skill
  should be used when reviewing skill PRs, auditing skill design, or validating
  skill issues. Trigger phrases include "review skill PR", "audit skill", "check
  skill quality", "validate issue".
---

# Skill Reviewer

Reviews Claude Code skills using per-file agents. Each agent reviews one file for ALL applicable design principles, then issues are validated and aggregated.

## Modes

| Mode | Input | Purpose |
|------|-------|---------|
| `pr` | PR number or URL | Review changes in a skill-modifying PR |
| `audit` | Skill path or name | Full audit of existing skill |
| `issue` | Issue number or URL | Validate issue claims against skill code |

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Target | Yes | PR number/URL, skill path/name, or issue number/URL |
| Repository | No | Defaults to current repo's remote (for PR/issue modes) |

## Workflow

```
- [ ] Step 0: Detect mode from input
- [ ] Step 1: Gather context (mode-specific)
- [ ] Step 2: Per-file review (parallel agents)
- [ ] Step 3: Validate issues (filter false positives)
- [ ] Step 4: Aggregate and output (mode-specific report)
```

Use TodoWrite to track progress through these steps.

---

## Step 0: Detect Mode

Determine mode from input:

| Input Pattern | Mode | Example |
|--------------|------|---------|
| Number (1-6 digits) | `pr` | `123` |
| URL containing `/pull/` | `pr` | `github.com/org/repo/pull/123` |
| URL containing `/issues/` | `issue` | `github.com/org/repo/issues/456` |
| Path containing `.claude/skills/` | `audit` | `.claude/skills/my-skill` |
| Path containing `skills/` | `audit` | `skills/my-skill` |
| Name (letters/hyphens only) | `audit` | `my-skill` |

If ambiguous, ask user: "Is this a PR number, issue number, or skill name?"

---

## Step 1: Gather Context

### PR Mode (Haiku)

Launch a **Haiku** subagent:

```
Analyze PR #{number} on {repo}.

1. Run: gh pr view {number} --repo {repo} --json title,body,files,baseRefName
2. Run: gh pr diff {number} --repo {repo}

Return structured JSON:
{
  "mode": "pr",
  "pr_title": "...",
  "pr_description": "...",
  "skill_files": [
    {"path": "...", "type": "SKILL.md|reference|script|other"}
  ],
  "file_count": N
}

If no skill files changed: {"mode": "pr", "exit": "NO_SKILL_FILES_CHANGED"}
```

If `exit` is set, stop and report: "This PR does not modify skill files."

### Audit Mode (Haiku)

Launch a **Haiku** subagent:

```
Enumerate skill at {skill_path}.

1. Find SKILL.md: ls {skill_path}/SKILL.md
2. List references: ls {skill_path}/references/ 2>/dev/null
3. List scripts: ls {skill_path}/scripts/ 2>/dev/null
4. List other files: find {skill_path} -type f | grep -v -E '(SKILL\.md|references/|scripts/)'

For each file, read it to determine type and size.

Return structured JSON:
{
  "mode": "audit",
  "skill_name": "...",
  "skill_path": "...",
  "skill_files": [
    {"path": "...", "type": "SKILL.md|reference|script|other", "lines": N}
  ],
  "file_count": N
}
```

### Issue Mode (Sonnet)

Launch a **Sonnet** subagent (requires judgment to extract claims):

```
Analyze issue #{number} on {repo}.

1. Run: gh issue view {number} --repo {repo}
2. Identify which skill is referenced (look for paths, skill names)
3. Extract specific claims (bugs, design issues, improvements)
4. List skill files relevant to claims

Return structured JSON:
{
  "mode": "issue",
  "issue_title": "...",
  "issue_claims": [
    {"claim": "...", "relevant_files": ["..."]}
  ],
  "skill_path": "...",
  "skill_files": [
    {"path": "...", "type": "SKILL.md|reference|script|other"}
  ],
  "file_count": N
}

If no skill identifiable: {"mode": "issue", "exit": "NO_SKILL_IDENTIFIED"}
```

If `exit` is set, stop and report: "Could not identify which skill this issue references."

---

## Step 2: Per-File Review

### Strategy Selection

| File Count | Strategy |
|------------|----------|
| 1-8 | One agent per file |
| 9+ | Chunked: SKILL.md alone, others in groups of 3 |

### Model Assignment

| File Type | Model | Principles Checked |
|-----------|-------|-------------------|
| SKILL.md | Opus | All 6 (Sequencing, Context, LLM vs Code, Structure, Error Visibility, Recitation) |
| Reference | Sonnet | LLM vs Code, Structure |
| Script | Sonnet | LLM vs Code |
| Other | Haiku | Structure only |

### Mode Context

Include this context in every agent prompt:

| Mode | Context String |
|------|----------------|
| `pr` | `"PR Review: Focus on CHANGES introduced by this PR. Title: {pr_title}"` |
| `audit` | `"Full Audit: Review comprehensively. No pre-existing exemption."` |
| `issue` | `"Issue Validation: Validate these claims: {issue_claims}"` |

### Agent Prompts

Launch agents **in parallel** (single message, multiple Task tool calls).

**For SKILL.md (Opus):**

```
Review {skill_name}/SKILL.md for ALL skill design principles.

{mode_context}

{file_content_instruction}

Check for:

1. SEQUENCING
   - Validation that runs before its inputs exist
   - Forward dependencies (step needs output from later step)
   - Single steps handling multiple unrelated failure types
   - Steps accumulating context irrelevant to later work

2. CONTEXT MANAGEMENT
   - Main orchestrator instructed to read large files directly
   - Main orchestrator reading reference files (should be for subagents)
   - Work that should be delegated to subagents
   - run_in_background:true for subagents (pollutes context)
   - Inter-step state via conversation instead of artifacts

3. LLM VS CODE
   - Mutable skill files (templates, configs in skill directory)
   - Auto-detection bypassing intentional LLM choice
   - Wrong responsibility (LLM doing mechanical work, or vice versa)

4. STRUCTURE
   - Line count over 500
   - Nested references (refs from refs)
   - Absolute paths or backslashes
   - Invalid frontmatter (name, description)

5. ERROR VISIBILITY
   - Fix-loops that retry without logging failures to file
   - Subagent prompts that say "Done." without error counts
   - Prompts that discourage error reporting ("skip and continue")
   - No issues.md or equivalent for capturing failures

6. RECITATION (only if 5+ steps)
   - No progress.md or TodoWrite instruction for long pipelines
   - Progress file updated but never read back before steps
   - No workflow checklist with progress tracking

For each issue:
- Principle: SEQUENCING | CONTEXT_MANAGEMENT | LLM_VS_CODE | STRUCTURE | ERROR_VISIBILITY | RECITATION
- Line: {number or range}
- Anti-pattern: {specific violation}
- Recommendation: {concrete fix}
- Confidence: HIGH | MEDIUM

Also note positive patterns worth preserving.

If no issues: "NO_ISSUES_FOUND"
```

**For Reference Files (Sonnet):**

```
Review {file_path} for applicable skill design principles.

{mode_context}

{file_content_instruction}

Check for:

1. LLM VS CODE
   - Templates that instruct LLM to edit skill files
   - Wrong responsibility assignment

2. STRUCTURE
   - References to other reference files (nested refs)
   - Absolute paths or backslashes

For each issue:
- Principle: LLM_VS_CODE | STRUCTURE
- Line: {number or range}
- Anti-pattern: {specific violation}
- Recommendation: {concrete fix}
- Confidence: HIGH | MEDIUM

If no issues: "NO_ISSUES_FOUND"
```

**For Script Files (Sonnet):**

```
Review {file_path} for LLM VS CODE responsibility.

{mode_context}

{file_content_instruction}

Check for:
- Script doing judgment work that requires LLM interpretation
- Auto-detection that bypasses intentional LLM choice
- Missing validation that should be deterministic

For each issue:
- Principle: LLM_VS_CODE
- Line: {number or range}
- Anti-pattern: {specific violation}
- Recommendation: {concrete fix}
- Confidence: HIGH | MEDIUM

If no issues: "NO_ISSUES_FOUND"
```

### File Content Instructions

| Mode | {file_content_instruction} |
|------|---------------------------|
| `pr` | `"Get file content via: gh pr diff {number} --repo {repo}"` |
| `audit` | `"Read the file directly at: {file_path}"` |
| `issue` | `"Read the file directly at: {file_path}"` |

### Chunking (9+ Files)

When file count exceeds 8:

1. SKILL.md gets dedicated Opus agent
2. Group remaining files by directory (references/, scripts/, other)
3. Split each group into chunks of 3 files max
4. Launch one Sonnet agent per chunk

**Chunk Agent Prompt:**
```
Review these files from {skill_name}:

Files: {file_list}

{mode_context}

For each file, check applicable principles:
- Reference files: LLM vs Code, Structure
- Script files: LLM vs Code
- Other files: Structure only

Report issues grouped by file.
```

---

## Step 3: Validate Issues

Collect all issues from Step 2 agents.

### PR and Audit Modes

For each issue with **MEDIUM confidence**, launch a **Sonnet** validation agent:

```
Validate this potential issue:

Issue: {issue_description}
File: {file_path}
Line: {line_reference}
Anti-pattern: {anti_pattern}

{file_content_instruction}

Determine:
1. Is this actually an issue, or a false positive?
2. Does context justify this pattern (intentional tradeoff)?
3. [PR mode only] Is this pre-existing or introduced by this PR?

Return one of:
- VALID: {explanation}
- FALSE_POSITIVE: {explanation}
- PRE_EXISTING: {explanation} [PR mode only]
```

Filter out FALSE_POSITIVE and PRE_EXISTING issues.

### Issue Mode

**Skip validation step.** Issue mode validates claims, not skill issues.

For each agent that reviewed files related to a claim, extract:
- Claim validated
- Verdict: CONFIRMED | REFUTED | INCONCLUSIVE
- Evidence from code

---

## Step 4: Aggregate and Output

### PR Mode Report

```markdown
## Skill PR Review: #{number}

### Summary
{PR title and 1-sentence description}

### Critical Issues
{LLM vs Code violations that must be fixed}

### Important Issues
{Sequencing and Context Management issues}

### Minor Issues
{Structure issues and suggestions}

### Design Validation

| Principle | Verdict | Notes |
|-----------|---------|-------|
| Sequencing | Pass/Fail | {summary} |
| Context Management | Pass/Fail | {summary} |
| LLM vs Code | Pass/Fail | {summary} |
| File Structure | Pass/Fail | {summary} |
| Error Visibility | Pass/Fail | {summary} |
| Recitation | Pass/Fail/N/A | {summary} |

### Positive Observations
{Good patterns introduced by this PR}

### Recommendations
1. {Highest priority}
2. {Second priority}
3. {Third priority}
```

### Audit Mode Report

```markdown
## Skill Audit: {skill_name}

### Summary
{Skill purpose from frontmatter. N files reviewed.}

### Overall Health
{GREEN (no critical/important) | YELLOW (important issues) | RED (critical issues)}

### Critical Issues
{Issues that should be fixed immediately}

### Important Issues
{Issues that should be addressed}

### Minor Issues
{Suggestions and polish items}

### Design Validation

| Principle | Status | Issue Count |
|-----------|--------|-------------|
| Sequencing | Pass/Fail | N |
| Context Management | Pass/Fail | N |
| LLM vs Code | Pass/Fail | N |
| File Structure | Pass/Fail | N |
| Error Visibility | Pass/Fail | N |
| Recitation | Pass/Fail/N/A | N |

### Positive Observations
{Good patterns to preserve}

### Improvement Roadmap
1. {Highest impact fix}
2. {Second priority}
3. {Third priority}
```

### Issue Mode Report

```markdown
## Issue Validation: #{issue_number}

### Issue Summary
{Issue title}

### Claim Validation

| Claim | Verdict | Evidence |
|-------|---------|----------|
| {claim 1} | CONFIRMED/REFUTED/INCONCLUSIVE | {code evidence} |
| {claim 2} | ... | ... |

### Additional Findings
{Issues discovered while validating that weren't in the original issue}

### Recommendation
{CLOSE (claims invalid) | ACCEPT (claims valid) | NEEDS_DISCUSSION (mixed/unclear)}
```

---

## False Positives

See `references/false-positives.md` for patterns that look like issues but aren't.

---

## References

| File | Purpose |
|------|---------|
| `references/principles.md` | Detailed principle definitions with examples |
| `references/false-positives.md` | Patterns to ignore |
| `references/articles/` | Background reading on context engineering for agents |
