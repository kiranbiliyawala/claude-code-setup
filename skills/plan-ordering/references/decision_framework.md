# Plan Ordering Decision Framework - Research and Sources

This document provides the research foundation and sources for the plan ordering decision framework.

## Key Concepts

### Walking Skeleton / Tracer Bullet

A "walking skeleton" is an implementation of the thinnest possible slice of real functionality that can be built, deployed, and tested end-to-end. It establishes the architectural foundation that later work builds upon.

**Source:** [Start Your Project With a Walking Skeleton - Henrico Dolfing](https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html)

**Key insight:** "It makes sense to work on the riskiest parts of the project first, which are usually the parts which have dependencies: on third party services, on in house services, on other groups in the organization."

### Last Responsible Moment (LRM)

The strategy of delaying a decision until the moment when the cost of not making the decision is greater than the cost of making it.

**Sources:**
- [The Last Responsible Moment - Coding Horror](https://blog.codinghorror.com/the-last-responsible-moment/)
- [Last responsible moment (LRM) - Software Architect's Handbook](https://www.oreilly.com/library/view/software-architects-handbook/9781788624060/a844b94f-be9e-456d-8ef0-cd9b46b41c33.xhtml)
- [Lean Software Development: Before and After the Last Responsible Moment](https://effectivesoftwaredesign.com/2014/03/27/lean-software-development-before-and-after-the-last-responsible-moment/)

**Key insights:**
- "Decisions made too early in a project are hugely risky. Early decisions often result in work that has to be thrown away."
- "The last responsible moment makes sense for decisions which are costly to change."
- "Tactics for delaying commitment include: Use interfaces. Separate interfaces from implementations."

### Cost of Change

The effort, time, and resources required to modify a software system after it has been delivered or built.

**Sources:**
- [Examining the Agile Cost of Change Curve](https://agilemodeling.com/essays/costofchange.htm)
- [Cost of Change — The Hidden Driver Behind Our Software Delivery Choices](https://softwaredominos.com/home/software-design-development-articles/cost-of-change-the-hidden-driver-behind-our-software-delivery-choices/)

**Key insights:**
- Traditional view (Boehm): Cost of change rises exponentially over time
- Agile view: Cost curve can be flattened through iterative development and feedback loops
- XP goal: "Create conditions under which the cost of changing the software doesn't rise catastrophically"

### Clean Architecture on Deferring Decisions

**Source:** [Clean Architecture - Uncle Bob](https://blog.cleancoder.com/uncle-bob/2011/11/22/Clean-Architecture.html)

**Key insight:** "The purpose of a good architecture is to defer decisions... The job of an architect is not to make decisions, the job of an architect is to build a structure that allows decisions to be delayed as long as possible."

**Example:** When developing FitNesse, the team deferred the decision of which database to use for years. By the time the project finished, they realized they didn't need one—saving significant time and complexity.

### Make Choices, Defer Commitment

**Source:** [Make choices, defer commitment - Medium](https://medium.com/@tsodzawiczny/make-choices-defer-commitment-a9ef2ce924c0)

**Key insight:** "Choosing a technology is one thing, committing to it is another... The right question is not 'how useful is it right now', but rather: 'how hard will it be to replace'."

### YAGNI (You Aren't Gonna Need It)

**Sources:**
- [Yagni - Martin Fowler](https://martinfowler.com/bliki/Yagni.html)
- [YAGNI Principle - GeeksforGeeks](https://www.geeksforgeeks.org/software-engineering/what-is-yagni-principle-you-arent-gonna-need-it/)

**Key insights:**
- YAGNI applies to presumptive features, not to effort making software easier to modify
- "Yagni is only a viable strategy if the code is easy to change, so expending effort on refactoring isn't a violation"
- YAGNI requires continuous refactoring, automated testing, and continuous integration to avoid technical debt

**Note for this skill:** YAGNI governs *scope* (whether to build something). This skill governs *ordering* (when to build committed work).

## Application to Multi-Phase Implementation

When all phases are pre-planned and committed:

1. **YAGNI doesn't directly apply** - The work is already in scope
2. **LRM applies to design decisions within work** - Defer detailed design where uncertainty exists
3. **Walking Skeleton applies to ordering** - Build foundational paths early
4. **Cost of Change applies to retrofit analysis** - Evaluate structural impact of deferral

## Decision Priority Order

Based on the research, evaluate in this order:

1. **Dependency Direction** - What depends on what? (Walking Skeleton)
2. **Retrofit Cost** - Will deferring cause rework? (Cost of Change)
3. **Information Gain** - Will waiting yield better decisions? (LRM)
4. **Risk/Integration** - Where is uncertainty highest? (Tracer Bullet)
5. **Cognitive Focus** - Does inclusion blur phase purpose? (Clean Architecture)

## Additional References

- [When Deferring Decisions Leads to Better Codebases - InfoQ](https://www.infoq.com/news/2019/10/reactiveconf-2019-delay-decision/)
- [Deferring architecture decisions - Kalle Marjokorpi](https://www.kallemarjokorpi.fi/blog/deferring-architecture-decisions/)
- [Cost of Delay - Scaled Agile Framework](https://framework.scaledagile.com/blog/glossary_term/cost-of-delay/)
- [Walking skeletons and tracer bullets - Tinned Fruit](https://tinnedfruit.com/list/20180815)
- [Tracer bullets - Barbaric Meets Coding](https://www.barbarianmeetscoding.com/notes/books/pragmatic-programmer/tracer-bullets/)
