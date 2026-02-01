# Claude Code User Instructions

## GitHub Operations

Always use the GitHub CLI (`gh`) for all GitHub operations instead of MCP GitHub tools. The `gh` CLI is properly authenticated and more reliable.

Examples:
- `gh pr view <number> --repo <owner/repo>` - View PR details
- `gh pr diff <number> --repo <owner/repo>` - Get PR diff
- `gh pr list --repo <owner/repo>` - List PRs
- `gh issue list --repo <owner/repo>` - List issues
- `gh api repos/<owner>/<repo>/pulls/<number>/comments` - Get PR comments
