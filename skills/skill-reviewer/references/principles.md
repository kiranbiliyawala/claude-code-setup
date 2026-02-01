# Skill Design Principles

Detailed definitions and examples for each principle reviewed.

## 1. Sequencing

**Goal:** Steps should be ordered to minimize wasted work and enable independent re-runs.

### What Good Looks Like

- Each step has access to all inputs it needs
- Validation happens at the earliest point where required artifacts exist
- Different failure surfaces are separated into different steps
- Steps can be re-run independently without re-running earlier steps

### Anti-Patterns

**Forward Dependencies**
```markdown
# Bad: Step 2 needs output from Step 3
Step 2: Validate auth config  ← needs .env
Step 3: Create .env file
```

**Mixed Failure Surfaces**
```markdown
# Bad: One step handles unrelated failures
Step 6: Validate with Schemathesis
  - Fix schema errors (failure surface A)
  - Fix link errors (failure surface B)
  - These accumulate irrelevant context for each other
```

**Better Design**
```markdown
# Good: Separate steps for separate concerns
Step 6: Schema validation (fix-loop for schema/auth)
Step 7: Link validation (fix-loop for links)
  - Can re-run Step 7 without re-running Step 6
  - Context stays relevant to current task
```

### Example Feedback

> "Step 2 validates auth, but `.env` isn't created until Step 3. Move validation to Step 3 end."

> "Examples validation and stateful validation have different failure surfaces. Consider splitting into separate steps with separate agent invocations."

---

## 2. Context Management

**Goal:** Keep orchestrator context thin; delegate heavy reading to subagents.

### What Good Looks Like

- Main orchestrator only: runs scripts, coordinates subagents, reads small outputs
- Large files (>1KB) processed by subagents, not orchestrator
- Reference files are for subagents to read, not the main agent
- Inter-step state passes via artifacts (files), not accumulated context
- Subagents run in foreground (background returns full tool history)

### Anti-Patterns

**Orchestrator Reading Large Files**
```markdown
# Bad
Step 2: Read input/partner-api.md and extract server URLs
```

**Orchestrator Reading Reference Files**
```markdown
# Bad
Before Step 3, review references/step3-endpoints.md to understand the format
```

**Background Subagents**
```markdown
# Bad: Returns full tool history to main context
Launch subagent with run_in_background: true
```

**Better Design**
```markdown
# Good: Delegate to subagent with file path
Launch Haiku subagent:
  "Read {run_dir}/input/partner-api.md and extract server URLs.
   See .claude/skills/.../references/step2-globals.md for format."
```

### Example Feedback

> "This cannot be done by the main orchestrator. This will consume its context without good reason."

> "Long fix-loops in examples accumulate context irrelevant to stateful testing. Pass state via a context file instead."

---

## 3. LLM vs Code Responsibility

**Goal:** Code handles deterministic work; LLM handles interpretation and judgment.

### What Good Looks Like

- Skills are immutable—no runtime edits to skill files
- Patterns/config are data (YAML) stored OUTSIDE skill directory
- LLM is intentional—not allowed to skip explicit decisions
- Validation scripts handle mechanical checks
- LLM handles interpretation, debugging, judgment calls

### Anti-Patterns

**Mutable Skill Files (Critical)**
```
# Bad: Templates in skill directory can be edited
.claude/skills/my-skill/
├── SKILL.md
├── templates/           ← LLM can edit these
│   └── patterns.yaml    ← Changes persist across ALL runs
└── scripts/
```

Even if you "copy to run dir first", the SOURCE can still be edited.

**Auto-Detection Bypassing Intentionality**
```python
# Bad: LLM can skip explicit pattern choice
def detect_patterns(content):
    if "json" in content.lower():
        return JSON_PATTERNS  # Auto-detected, LLM didn't choose
```

**Wrong Responsibility Assignment**
```markdown
# Bad: LLM doing mechanical work
Step 3: Count the lines in SKILL.md and verify under 500

# Good: Script does mechanical work
Run: wc -l SKILL.md | awk '{if ($1 > 500) exit 1}'
```

### Example Feedback

> "Patterns should not live in skill directory. If Claude edits these during a run, changes persist and affect ALL future runs for ALL partners."

> "Don't autodetect. Let the LLM be intentional about which patterns to use. Will ensure they pay attention to it."

---

## 4. File Structure

**Goal:** Skills follow standard structure for discoverability and maintainability.

### Requirements

| Requirement | Validation |
|-------------|------------|
| SKILL.md under 500 lines | `wc -l SKILL.md` |
| References one level deep | No `$ref` in reference files |
| Forward slashes in paths | No `\` characters |
| No absolute paths | No paths starting with `/` or `~` |
| Valid frontmatter name | lowercase-hyphens, max 64 chars |
| Valid description | max 1024 chars, third person |
| Description has triggers | Includes "when to use" and trigger phrases |

### Anti-Patterns

**Too Long**
```markdown
# Bad: 800-line SKILL.md
Everything in one file, no progressive disclosure
```

**Nested References**
```markdown
# Bad: reference file references another reference
# references/step2.md
See references/step2-details.md for more info
```

**Wrong Path Format**
```markdown
# Bad
See .claude\skills\my-skill\references\foo.md
See /Users/me/.claude/skills/my-skill/SKILL.md
```

**Poor Description**
```yaml
# Bad: No triggers, second person
description: You can use this to review PRs

# Good: Triggers, third person
description: Reviews pull requests for skill design. This skill should be used when reviewing skill PRs or auditing skill architecture. Trigger phrases include "review skill PR", "check skill design".
```

---

## Mode-Specific Application

How to apply these principles varies by review mode.

### PR Mode

**Focus:** Changes introduced by the PR only.

| Principle | Application |
|-----------|-------------|
| Sequencing | Check if new/modified steps create forward dependencies |
| Context Management | Check if changes add orchestrator file reads |
| LLM vs Code | Check if new files are mutable, new auto-detection added |
| Structure | Check line count delta, new paths format |

**Key question:** "Does this PR make the skill worse?"

Do NOT flag pre-existing issues. The goal is to prevent regressions, not audit history.

### Audit Mode

**Focus:** Comprehensive review of current state.

| Principle | Application |
|-----------|-------------|
| Sequencing | Review entire workflow for all dependency issues |
| Context Management | Check all orchestrator instructions |
| LLM vs Code | Review all files in skill directory |
| Structure | Full validation of all structural requirements |

**Key question:** "Is this skill well-designed?"

Flag all issues regardless of when they were introduced.

### Issue Mode

**Focus:** Validate specific claims made in the issue.

| Principle | Application |
|-----------|-------------|
| All | Only check principles relevant to the issue's claims |

**Key question:** "Is the issue's claim accurate?"

Report whether each claim is CONFIRMED, REFUTED, or INCONCLUSIVE with evidence from the code.

---

## 5. Error Visibility

**Goal:** Failures should be logged and reported, not hidden.

### What Good Looks Like

- Fix-loops log errors to `issues.md` or similar artifact before retrying
- Subagent prompts ask for error details, not just success confirmation
- Final reports reflect actual outcomes (partial success = partial success, not "Done")
- Errors are preserved in files even if not kept in conversation context

### Anti-Patterns

**Silent Retry**
```markdown
# Bad: Retry without logging
Step 6: Run validation
  - If fails, retry up to 3 times
  - Report "Done." when passing
```
No record of what failed or why. Makes debugging impossible.

**Optimistic Reporting**
```markdown
# Bad: Subagent reports success despite partial failure
"Respond with only: 'Done.' or error details."

# Actual behavior: Subagent enriched 8/10 endpoints,
# but says "Done." because it technically finished
```

**Hidden Subagent Errors**
```markdown
# Bad: Prompt discourages error reporting
"Focus on successes. Don't report minor issues."
"If you can't complete a step, skip it and continue."
```

**Better Design**
```markdown
# Good: Explicit error logging
Step 6: Run validation
  - On failure: log to issues.md with request/response details
  - Retry up to 3 times
  - Report: "Passed after N retries" or "Failed: see issues.md"

# Good: Subagent prompt asks for specifics
"Respond with: 'Done. Enriched N endpoints. M errors logged to issues.md.'"
```

### Example Feedback

> "This fix-loop retries silently. Add logging to issues.md before each retry so failures are traceable."

> "Subagent prompt says 'Done.' or error—but partial success is also possible. Ask for specifics: 'Done. N succeeded, M failed.'"

---

## 6. Recitation for Long Pipelines

**Goal:** Pipelines with 5+ steps should have progress tracking to prevent goal drift.

### What Good Looks Like

- A `progress.md` (or equivalent) file exists in the run directory
- Orchestrator updates progress after completing each step
- Orchestrator reads progress before each step decision
- Progress includes step name and brief outcome summary

### Anti-Patterns

**No Progress File**
```markdown
# Bad: 14-step pipeline with no progress tracking
Step 1: Initialize
Step 2: Extract signals
...
Step 14: Finalize
# Orchestrator has no way to recall what's done
```

**Write-Only Progress**
```markdown
# Bad: Updates progress but never reads it back
"After each step, append to progress.md"
# But no instruction to READ progress.md before next step
```

**Summary Only at End**
```markdown
# Bad: Progress written only after completion
Step 14: Write summary to progress.md
# No intermediate tracking
```

**Better Design**
```markdown
# Good: Read-write progress cycle
Before each step:
  1. Read progress.md to recall current state
  2. Execute step
  3. Update progress.md with outcome

Format:
## Completed
- Step 1: Initialize ✓ (run-acme-20260110)
- Step 2: Extract signals ✓ (127 signals)

## Current
- Step 3: Interpret globals

## Remaining
- Step 4: Validate config
...
```

### When This Applies

| Pipeline Length | Recitation Required? |
|-----------------|---------------------|
| 1-4 steps | No |
| 5+ steps | Yes |
| Subagent-heavy (each step is a subagent) | Maybe—if orchestrator context stays thin, less critical |

### Example Feedback

> "This skill has 12 steps but no progress tracking. Add progress.md with read-before-step and write-after-step instructions."

> "progress.md is updated but never read back. Add instruction to read progress.md at the start of each step decision."

---

## Background Reading

For deeper context on these principles, see the articles in `references/articles/`:

| Article | Relevant Principles |
|---------|---------------------|
| `manus-context-engineering.md` | Error visibility (keep failures visible), Recitation (todo.md pattern) |
| `vercel-removed-tools.md` | Context management (fewer tools = better) |
| `langchain-filesystem-context.md` | Context management (filesystem as scratchpad) |
| `langchain-deep-agents.md` | Recitation (todo list as attention manipulation) |
