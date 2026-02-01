---
name: confluence-search
description: Search Confluence documents and retrieve page content via CLI. Use when needing to find internal documentation, look up procedures, runbooks, RFCs, or retrieve knowledge from Confluence. Trigger phrases include "search confluence", "find documentation", "look up in wiki", "internal docs", or when the user mentions Confluence pages.
---

# Confluence Search

Search and retrieve Confluence documents programmatically. Outputs JSON for composition with jq and other CLI tools.

## When to Use This Skill

- Finding internal documentation, runbooks, or procedures
- Looking up RFCs, architecture decisions, or technical specs
- Discovering pages under a documentation folder
- Searching across spaces or within a specific space
- Retrieving page content for analysis or reference

## Prerequisites

Environment variables must be set:
- `ATLASSIAN_EMAIL` - Atlassian account email
- `ATLASSIAN_API_TOKEN` - API token from https://id.atlassian.com/manage-profile/security/api-tokens
- `ATLASSIAN_BASE_URL` - Atlassian instance URL (e.g., `https://yourorg.atlassian.net`)

## Common Workflows

### Finding Documentation on a Topic

```bash
# Search for pages mentioning "datadog"
scripts/confluence-search.py "datadog onboarding" -l 10

# If a result is a folder (empty body), list its children
scripts/confluence-search.py --children 4458352401
```

### Exploring a Documentation Hierarchy

```bash
# Find all pages under a parent page using CQL
scripts/confluence-search.py --cql "ancestor=4458352401"

# Get a page with its parent context
scripts/confluence-search.py -p 12345678
# Returns: {..., "parent_id": "...", "parent_title": "..."}
```

### Searching Within a Space

```bash
# List available spaces to find the right one
scripts/confluence-search.py --list-spaces -l 20

# Search within a specific space
scripts/confluence-search.py "deployment" -s SYS
```

### Retrieving Page Content

```bash
# Get page body as plain text
scripts/confluence-search.py -p 12345678

# Include body in search results (slower, fetches each page)
scripts/confluence-search.py "API documentation" -c
```

## Output Format

All output is JSON for easy composition with `jq`:

```bash
# Extract just titles
scripts/confluence-search.py "kubernetes" | jq '.[].title'

# Get the first matching page's body
PAGE_ID=$(scripts/confluence-search.py "setup guide" | jq -r '.[0].id')
scripts/confluence-search.py -p "$PAGE_ID" | jq -r '.body'

# Filter results by space
scripts/confluence-search.py "deployment" | jq '.[] | select(.space == "Systems")'
```

## Tips

- **Empty body on a page?** It's likely a folder. Use `--children ID` to list pages under it.
- **Too many results?** Filter by space with `-s SPACE_KEY` or use CQL for complex queries.
- **Long pages truncated?** Check the `truncated` and `total_length` fields in the output.
- **Need raw HTML?** Use `--raw` flag when fetching a page.

For complete flag reference, run: `scripts/confluence-search.py --help`
