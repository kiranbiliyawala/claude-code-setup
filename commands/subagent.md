Fan out safe, mechanical work to subagents while you keep ownership of the critical path.

What to do, in order:

1. Classify tasks

- Separate tasks into Simple vs Complex and Serial vs Parallelisable.
- Do a quick critical‑path pass: keep the serial critical path for yourself.

2. Choose where to use subagents

- Only use subagents for tasks that are Simple AND Parallelisable.
- Everything else (Simple+Serial, Complex+Serial, Complex+Parallelisable) stays with you until broken down further.

3. Prevent conflicts

- Assign non‑overlapping scopes: one agent per file/glob or clearly separated domain.
- Explicitly list files they may modify; everything else is read‑only.

4. Brief each subagent

- Include: objective, exact scope (files/areas), constraints, success criteria, and stop criteria.
- If stop criteria is hit, the agent must stop and report the failure with findings and partial artifacts.

5. Batch and validate

- Create up to 8 subagents per message by calling the task tool multiple times.
- After each batch completes, validate outputs, integrate, and re-run tests before spawning the next batch.

Notes

- Validate every batch before proceeding to the next.
- Keep ownership of integration, reviews, and the serial critical path.
