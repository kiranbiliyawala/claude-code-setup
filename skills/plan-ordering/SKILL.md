---
name: plan-ordering
description: Decision framework for ordering implementation phases and tasks. This skill should be used when planning multi-phase implementations, deciding whether to defer work to later phases, or ordering tasks within a plan. Trigger phrases include "order this plan", "what should I do first", "should I defer this", or when creating implementation plans with multiple phases.
---

# Plan Ordering

## Overview

This skill provides a decision framework for ordering implementation tasks across phases. It applies when all phases are pre-planned and committed—the question is not *whether* to build something, but *when* to build it relative to other work.

## Core Principle

When phases are sequential and nothing ships until all phases complete, the goal is to **minimize total effort and risk** by ordering work strategically. This differs from YAGNI (which governs scope) because the work is already committed.

## Decision Framework

When deciding whether to include work in the current phase or defer to a later phase, evaluate these dimensions in order:

### 1. Dependency Direction (Highest Priority)

**Question:** Do later phases depend on this, or does this depend on later phases?

| Situation | Recommendation |
|-----------|----------------|
| Feature X is needed by subsequent phases | Build now (foundation work) |
| Feature X only consumes outputs from current phase | Can defer |
| Feature X is independent/orthogonal | Evaluate other dimensions |

**Guideline:** Build the "walking skeleton" first—the thinnest end-to-end path that later work builds upon.

### 2. Retrofit Cost

**Question:** Will deferring require modifying code written in earlier phases?

| Situation | Recommendation |
|-----------|----------------|
| Later addition requires restructuring earlier code | Build now to avoid rework |
| Later addition plugs in without touching earlier code | Safe to defer |
| Uncertain about integration points | Define interfaces now, defer implementation |

**Key insight:** If the current phase's code structure would differ based on whether this feature exists, include it now.

### 3. Information Gain

**Question:** Will building other pieces first reveal better design decisions?

| Situation | Recommendation |
|-----------|----------------|
| Design is well-understood | No benefit to deferring |
| Design depends on learnings from other work | Defer to gain information |
| Multiple valid approaches, unclear which is best | Defer, but define interface/contract now |

**Guideline:** Defer when uncertainty is high and later work will reduce that uncertainty.

### 4. Risk and Integration

**Question:** Does this involve external dependencies or integration uncertainty?

| Situation | Recommendation |
|-----------|----------------|
| External APIs, third-party services | Build early to surface problems |
| Infrastructure/environment dependencies | Build early to validate assumptions |
| Well-understood internal logic | Safe to defer |

**Guideline:** De-risk early. Integration surprises are cheaper to fix when less code exists.

### 5. Cognitive Focus

**Question:** Does including this blur the purpose of the current phase?

| Situation | Recommendation |
|-----------|----------------|
| Feature is orthogonal to phase's core purpose | Defer for clarity |
| Feature deeply interleaves with current work | Include to avoid context-switching |
| Feature is small and related | Include if it won't distract |

**Guideline:** Phases should have coherent themes. Mixing unrelated concerns increases cognitive load.

## Quick Decision Flowchart

Apply this sequence when evaluating each piece of work:

```
1. Is this part of the "skeleton" that later phases build on?
   ├── Yes → Include in current phase
   └── No → Continue...

2. Will deferring require modifying code from earlier phases?
   ├── Yes (high retrofit cost) → Include now
   └── No → Continue...

3. Will you learn something from other work that changes this design?
   ├── Yes → Defer (information gain)
   └── No → Continue...

4. Does it involve external dependencies or integration risk?
   ├── Yes → Include now (de-risk early)
   └── No → Continue...

5. Can you define a clean interface now and defer implementation?
   ├── Yes → Define interface now, defer implementation
   └── No → Apply default heuristic below
```

## Default Ordering Heuristic

When the framework doesn't yield a clear answer:

| Category | Recommendation |
|----------|----------------|
| Structural decisions (data models, abstractions, interfaces) | Early |
| Behavioral decisions (algorithms, business logic) | Can be later |
| Integration points (external APIs, infrastructure) | As early as possible |
| Polish and refinement (error messages, logging, edge cases) | As late as possible |

## Interface-First Strategy

When deferring implementation but needing to unblock other work:

1. **Define the contract** in the current phase (types, method signatures, expected behavior)
2. **Stub the implementation** with minimal working code or explicit `NotImplemented` markers
3. **Implement fully** in the designated later phase

This approach captures design decisions early while deferring implementation effort.

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Deferring all hard work | Risk accumulates at the end | Spread risk across phases |
| Including everything "just in case" | Phases become unfocused | Respect phase themes |
| Deferring without interface definition | Later phases guess at contracts | Define interfaces early |
| Ignoring retrofit cost | Creates hidden rework | Evaluate structural impact |

## Resources

Refer to `references/decision_framework.md` for the detailed research and sources behind this framework.
