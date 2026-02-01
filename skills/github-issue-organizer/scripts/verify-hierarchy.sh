#!/bin/bash
# Verify sub-issue hierarchy for a parent issue
# Usage: ./verify-hierarchy.sh OWNER REPO ISSUE_NUMBER [MAX_DEPTH]

set -euo pipefail

OWNER="${1:?Owner required}"
REPO="${2:?Repo required}"
ISSUE_NUMBER="${3:?Issue number required}"
MAX_DEPTH="${4:-2}"  # Default to 2 levels deep

# Build nested query based on depth
build_subissues_fragment() {
    local depth=$1
    local fragment="subIssues(first: 100) { nodes { number title state"

    if [ "$depth" -gt 1 ]; then
        local next_depth=$((depth - 1))
        fragment+=" $(build_subissues_fragment $next_depth)"
    fi

    fragment+=" } }"
    echo "$fragment"
}

query="query {
  repository(owner: \"$OWNER\", name: \"$REPO\") {
    issue(number: $ISSUE_NUMBER) {
      number
      title
      state
      $(build_subissues_fragment $MAX_DEPTH)
    }
  }
}"

# Execute and format output
echo "Fetching hierarchy for issue #${ISSUE_NUMBER}..."
gh api graphql -f query="$query" | jq -r '
  def print_issue(indent):
    indent + "#\(.number): \(.title) (\(.state))",
    (.subIssues.nodes[]? | print_issue(indent + "  "));

  .data.repository.issue | print_issue("")
'
