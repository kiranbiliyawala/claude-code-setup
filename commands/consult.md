---
description: Create a consultation document for external review
argument-hint: "[additional context]"
---

I want to get a consolation for our problem. $ARGUMENTS

**Success criterion**: Create EXACTLY 2 files (1 .md + 1 .txt), no extras

<critical_requirements>
**FILE STRUCTURE**:

- ONE .md file with ALL consultation content (problem + options + design + questions)
- ONE .txt file with ONLY verbatim code
- NO separate README, summary, index, or design files

**CONTEXT FILE (.txt) REQUIREMENTS**:

- MUST contain ONLY verbatim code copied from source files
- NO prose descriptions, summaries, or interpretations
- NO explanations of what the code does
- USE bash commands (sed, cat, grep, etc.) to extract code sections character-for-character
  </critical_requirements>

<steps>
1. Create ONE markdown file in root (e.g., CONSULTATION.md) containing:
   - Problem description
   - Solution options (if applicable) - clarify these are illustrative, welcome other recommendations
   - Detailed design (if solution requires it)
   - Questions for consultant
   - **System context**: Unreleased (pre-production), human-triggered, low-scale
   - **CRITICAL**: Reviewer is EXTERNAL with NO codebase access
   - **Emphasis**: Prioritize CORRECT approach over migration/compatibility concerns

2. Create ONE text file in root (e.g., CONTEXT.txt) using ONLY bash commands to copy verbatim code
   </steps>

<consultation_writing_guidelines>
**Audience**: External expert consultant WITHOUT codebase access

**Questions must be**:

- Answerable by external expert without running tools/searches
- Focused on "what should I do?" not "what should we check?"
- About patterns, principles, and industry standards

**Anti-patterns to avoid**:

❌ WRONG: "Check the codebase for other instances of this pattern"
✅ RIGHT: "Is this pattern an anti-pattern I should avoid elsewhere?"

❌ WRONG: "Here's the migration path from current to new approach..."
✅ RIGHT: "Given the system is unreleased, which approach is industry-standard?"

❌ WRONG: "Scan for all uses of asyncio.create_task() with request-scoped resources"
✅ RIGHT: "Is fire-and-forget with request-scoped resources a known anti-pattern?"

**For unreleased systems**:

- Focus on "doing it right" not "fixing what exists"
- Don't discuss migration complexity or backward compatibility
- Ask for the CORRECT pattern, not compromise solutions
  </consultation_writing_guidelines>

<context_file_format>
**CORRECT APPROACH** - Use bash to extract verbatim code:

```bash
cat > CONTEXT.txt << 'EOF'
=== File: src/hooks/useFormData.ts (lines 73-118) ===
EOF
sed -n '73,118p' src/hooks/useFormData.ts >> CONTEXT.txt
```

**NEVER write prose** like "This section handles polling" or "Purpose: Manages dirty tracking"
</context_file_format>

<examples>
**CORRECT FILE STRUCTURE**:
```
project-root/
├── CONSULTATION.md    ← All prose: problem, options, design, questions
└── CONTEXT.txt        ← Only verbatim code
```

**CORRECT context file** (verbatim code):

```
================================================================================
FILE: useFormData.ts - Lines 73-118
================================================================================

const {
enablePolling: startPolling,
disablePolling: stopPolling,
updateLocalRevision,
} = useSubmissionSync({
submissionId,
pollingInterval: 5000,
```

</examples>

<implementation_checklist>
Before completing, verify:

- [ ] Created EXACTLY 2 files (1 .md + 1 .txt), no extras
- [ ] Context file has ONLY verbatim code extracted via bash commands (no prose)
- [ ] All code sections are character-for-character copies from source
- [ ] Questions are answerable by external expert WITHOUT codebase access
- [ ] For unreleased systems: focused on "correct approach" not migration/compatibility
- [ ] Emphasized getting the RIGHT answer over pragmatic compromises
      </implementation_checklist>
