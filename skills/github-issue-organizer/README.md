# GitHub Issue Organizer

A Claude Code skill for analyzing and reorganizing GitHub issues into hierarchical sub-issue structures.

## Overview

This skill helps consolidate fragmented GitHub issues into well-organized epics with clear hierarchies. It uses GitHub's sub-issues feature (released January 2025) via the GraphQL API.

## What This Skill Does

When you ask Claude to organize GitHub issues, this skill provides:
- **Systematic workflow** for analyzing and grouping issues
- **GraphQL API patterns** for building issue hierarchies
- **Helper scripts** for efficient batch operations
- **Best practices** for quality parent issue content
- **Real-world examples** demonstrating the approach

## Skill Structure

```
github-issue-organizer/
├── SKILL.md                    # Core workflow (Claude reads this)
├── README.md                   # This file (user documentation)
├── scripts/                    # Helper scripts for automation
│   ├── get-node-ids.sh        # Batch query GraphQL node IDs
│   ├── link-sub-issues.sh     # Link multiple issues to parent
│   └── verify-hierarchy.sh    # Display issue hierarchy
├── templates/                  # Issue templates
│   └── parent-issue-template.md  # Template for epic/group issues
└── references/                 # Detailed documentation (loaded as needed)
    ├── graphql-api.md         # Complete GraphQL patterns
    ├── best-practices.md      # Quality guidelines and patterns
    └── case-study.md          # Real-world example walkthrough
```

## When Claude Uses This Skill

Claude automatically activates this skill when you ask to:
- "Organize my GitHub issues into epics"
- "Consolidate fragmented issues"
- "Analyze and group related GitHub issues"
- "Create a hierarchy for my project backlog"

## Progressive Disclosure Design

The skill uses a three-level loading system for efficiency:

1. **Metadata** (always loaded) - Skill name and description
2. **SKILL.md** (loaded when skill triggers) - Core workflow and references
3. **References** (loaded as needed) - Detailed patterns and documentation

This keeps Claude's context efficient while providing deep expertise on demand.

## Key Improvements in v2

This version applies best practices from the skill-creator guidance:

### Structure
- **Lean SKILL.md** - Reduced from 9.5KB to ~5KB by moving details to references
- **Progressive disclosure** - Detailed content in references/, loaded only when needed
- **No duplication** - Information lives in one place, referenced from SKILL.md

### Content
- **Imperative form** - Rewritten from second-person to verb-first instructions
- **Better organization** - GraphQL, best practices, and case study separated
- **Grep patterns** - Quick navigation within large reference files

### Workflow
- **Clearer script usage** - Explicit triggers for when to use each script
- **Reference guidance** - Clear instructions on when to load detailed docs
- **Validated structure** - Follows skill-creator validation requirements

## Usage Examples

### Example 1: Organize scattered issues
```
You: "I have 30 issues about testing scattered across my repo. Help me organize them."

Claude: [Activates skill]
- Fetches and analyzes issues
- Groups by theme (unit tests, integration tests, coverage)
- Creates parent epic with architectural guidance
- Uses scripts to build hierarchy
- Verifies and shows results
```

### Example 2: Create new epic
```
You: "Create an epic for OpenTelemetry observability work"

Claude: [Activates skill]
- Uses parent-issue-template.md
- Fills in comprehensive architectural guidance
- Creates GitHub issue
- Links existing related issues as sub-issues
```

### Example 3: Understand the approach
```
You: "How would you organize API-related issues?"

Claude: [Activates skill]
- Loads references/case-study.md
- Shows real-world REST API example
- Explains grouping rationale (error handling, caching, etc.)
- Demonstrates 2-level hierarchy pattern
```

## Helper Scripts

All scripts are executable and well-documented:

### get-node-ids.sh
Batch query for GraphQL node IDs (required before mutations):
```bash
./scripts/get-node-ids.sh dreamplug-tech weave "106 107 108 109"
```

### link-sub-issues.sh
Link multiple issues to a parent in one operation:
```bash
./scripts/link-sub-issues.sh "I_kwDOPdtIAs7SF8sD" "I_kwDOPdtIAs7SF9uh I_kwDOPdtIAs7SF9ul"
```

### verify-hierarchy.sh
Display issue hierarchy with formatting:
```bash
./scripts/verify-hierarchy.sh dreamplug-tech weave 106 2
```

## Installation

This skill is a user-level skill, available across all projects when using Claude Code.

**Location:**
```
~/.claude/skills/github-issue-organizer/
```

## Testing

To test the skill, ask Claude:
```
"Analyze my GitHub issues and recommend how to organize them into epics"
```

Claude should automatically load this skill and follow the workflow in SKILL.md.

## Customization

Customize the skill for your needs:
- **SKILL.md** - Adjust workflow or add project-specific patterns
- **Scripts** - Modify for your repository conventions
- **Templates** - Tailor to your team's issue format
- **References** - Add your own patterns or case studies

Changes take effect immediately in new Claude Code sessions.

## Version History

- **v2.0.0** - Complete refactor applying skill-creator best practices
  - Progressive disclosure architecture
  - Imperative writing style
  - Separated concerns (SKILL.md, references, scripts)
  - Improved grep-ability and discoverability

- **v1.0.0** - Initial version
  - Monolithic SKILL.md with all content inline
  - Second-person writing style
  - Some duplication between files

## Resources

- [GitHub Sub-Issues Announcement](https://github.blog/changelog/2025-01-15-sub-issues-public-beta/)
- [GraphQL API Reference](https://docs.github.com/en/graphql)
- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
