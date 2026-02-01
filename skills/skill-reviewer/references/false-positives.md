# False Positives - Do NOT Flag

Patterns that look like issues but are acceptable or intentional.

## Sequencing

**Acceptable: Conditional steps**
```markdown
Step 6b: Stateful validation (only if has_links)
```
This isn't a forward dependency—it's a conditional skip.

**Acceptable: Shared validation**
```markdown
Step 4: Enrich endpoint
  - Validate after enrichment
```
Validation within a step is fine; the concern is validation in a SEPARATE step before inputs exist.

---

## Context Management

**Acceptable: Small config files**
```markdown
Step 1: Read .env to get BASE_URL
```
Small files (<1KB) are fine for orchestrator to read.

**Acceptable: Script output**
```markdown
Step 3: Run endpoint_signals.py, read endpoints.txt
```
Reading script OUTPUT is fine—the concern is reading large INPUT files.

**Acceptable: Explicit path passing**
```markdown
Launch subagent: "Read {run_dir}/input/partner-api.md"
```
Passing a path to a subagent is correct—the subagent reads, not orchestrator.

---

## LLM vs Code

**Acceptable: Read-only templates**
```markdown
.claude/skills/my-skill/
├── templates/
│   └── skeleton.yaml  ← Read-only template copied to run dir
```
If the SKILL.md never instructs editing the template (only copying), this is fine.

**Acceptable: Scripts in skill directory**
```markdown
.claude/skills/my-skill/
├── scripts/
│   └── validate.py
```
Python scripts are fine—they're executed, not edited by LLM.

**Acceptable: Conditional logic based on artifacts**
```python
# OK: Decision based on artifact content
if grep -q "links:" openapi.yaml:
    run_stateful = True
```
This is deterministic code making a decision, not LLM auto-detection.

**Acceptable: LLM choosing from explicit options**
```markdown
Step 2: Review the pattern options below and select appropriate ones:
  - Pattern A: For REST APIs with versioned paths
  - Pattern B: For GraphQL endpoints
  - Pattern C: For webhook receivers
```
Explicit options with LLM choosing is GOOD—the concern is implicit auto-detection.

---

## File Structure

**Acceptable: Long reference files**
```markdown
references/step6-validation.md  ← 486 lines
```
Reference files can be longer—the 500-line limit is for SKILL.md only.

**Acceptable: Multiple reference levels if flat**
```markdown
references/
├── principles/
│   ├── sequencing.md
│   └── context.md
└── examples/
    └── good-skill.md
```
Subdirectories for organization are fine—the concern is references that IMPORT other references.

---

## General

**Pre-existing issues**

Don't flag issues that exist in unchanged code. The PR review should focus on CHANGES introduced by the PR.

**Intentional tradeoffs**

If the PR description or commit message explains why a pattern is used, consider it intentional:
```
"Using sequential validation here because parallel would require shared state"
```

**Work in progress**

Draft PRs or PRs marked WIP may have temporary patterns that will be fixed before merge.

---

## Mode-Specific False Positives

### PR Mode

**Pre-existing issues (Critical)**

Never flag issues in unchanged code. If a pattern existed before this PR, it's out of scope:
```
# Out of scope in PR mode
- Issues on lines not modified by the PR
- Patterns that exist in the base branch
- Structural issues present before the PR
```

Use `git diff` or `gh pr diff` to verify what actually changed.

### Audit Mode

**Documented limitations**

If a skill explicitly documents a limitation or intentional tradeoff in comments, don't flag it as an issue:
```markdown
<!-- Intentionally using sequential validation here because
     parallel would require shared state between validators -->
Step 5: Run validators in sequence
```

The key is explicit documentation. Undocumented deviations are still issues.

**Historical context**

Unlike PR mode, audit mode DOES flag all issues regardless of when introduced. "This was always like this" is not a valid excuse in audit mode.

### Issue Mode

**Unrelated findings**

When validating issue claims, don't report every issue you find in the skill. Only report:
1. Evidence confirming or refuting the specific claims
2. Issues directly related to the claims
3. Critical issues (severity = blocking) even if unrelated

```
# Issue claims: "SKILL.md has forward dependencies in Step 2-3"

# Good: Report evidence about Step 2-3 dependencies
# Bad: Report unrelated context management issue in Step 5
# Exception: If Step 5 has a critical immutability violation, still report it
```

**Partial claims**

If an issue claim is partially correct, report it as INCONCLUSIVE with evidence for both sides:
```
Claim: "Step 3 validates before inputs exist"
Verdict: INCONCLUSIVE
Evidence:
- Step 3 does validate early (supporting claim)
- But the inputs ARE created in Step 2, not Step 3 (refuting claim)
- The issue may be referring to a different version of the skill
```

---

## Error Visibility

**Acceptable: Summarized errors**
```markdown
"Report: 'Done. N succeeded, M failed. See issues.md for details.'"
```
Errors are preserved in a file—just not inline in the response. This is fine.

**Acceptable: Single-attempt steps**
```markdown
Step 3: Run extraction script
  - If fails, stop and report error
```
No retry means no silent retry. Failing loudly is correct behavior.

**Acceptable: Documented retry limits**
```markdown
Step 6: Validation loop (max 3 attempts)
  - On failure: log to issues.md, then retry
  - After 3 failures: stop and report
```
Retries are fine if failures are logged before each retry.

**Acceptable: Subagent error aggregation**
```markdown
"If multiple errors occur, summarize count and log details to issues.md"
```
Summarizing is fine if details are preserved somewhere.

---

## Recitation

**Acceptable: Short pipelines**
```markdown
# 3-step skill - no progress.md needed
Step 1: Initialize
Step 2: Process
Step 3: Finalize
```
Recitation is for 5+ steps. Short pipelines stay in context naturally.

**Acceptable: Subagent-heavy pipelines**
```markdown
# Each step is a subagent with narrow scope
Step 1: [Haiku] Extract globals
Step 2: [Haiku] Extract endpoints
Step 3: [Haiku×N] Enrich endpoints
Step 4: [Opus] Validate
```
If orchestrator context stays thin (just launches subagents), recitation is less critical.

**Acceptable: TodoWrite instead of progress.md**
```markdown
Use TodoWrite to track progress through these steps.
```
Claude Code's TodoWrite serves the same purpose as progress.md. Either works.

**Acceptable: Workflow checklist in SKILL.md**
```markdown
## Workflow
- [ ] Step 1: Initialize
- [ ] Step 2: Extract
...
```
If the skill instructs "Use TodoWrite to track progress" alongside the checklist, this satisfies recitation.
