---
description: Validate bug reports or code review comments against actual implementation
argument-hint: [bug-report or review-comment]
---

Evaluate this report/comment against actual code:

$ARGUMENTS

**Validation checklist:**

1. Locate referenced file(s) and line numbers
2. Examine actual code - does the report's claim hold true?
3. Check if tests exist that would catch this issue - run them if yes
4. If no test exists, write a minimal test case. Run the type checker on the test case to catch any blocking type issues before you run the test.
5. Determine severity and impact on system
6. Research best practices via web search before forming recommendation

**Test disposition:**

- **If bug is VALID**: Convert the test case into a proper regression test:
  - Name it descriptively (e.g., `test_<module>_<bug_description>`)
  - Place it in the appropriate test file/directory
  - Add a brief comment referencing the original report
  - Ensure it fails before the fix and passes after
- **If bug is INVALID**: Delete the test case (it served its validation purpose)

**Output format:**

- VALID/INVALID with clear reasoning
- Code evidence (exact lines from files)
- Test findings (existing or new)
- Recommended action
