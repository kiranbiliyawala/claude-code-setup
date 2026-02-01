#!/bin/bash
# Get GraphQL node IDs for multiple GitHub issues
# Usage: ./get-node-ids.sh OWNER REPO "106 107 108 109"

set -euo pipefail

OWNER="${1:?Owner required}"
REPO="${2:?Repo required}"
ISSUE_NUMBERS="${3:?Issue numbers required (space-separated string)}"

# Build GraphQL query dynamically
query="query {"
query+="repository(owner: \"$OWNER\", name: \"$REPO\") {"

# Add each issue to the query
for num in $ISSUE_NUMBERS; do
    # Use issue number as alias to make results clear
    query+="issue_${num}: issue(number: $num) { id number title } "
done

query+="} }"

# Execute query
gh api graphql -f query="$query" --jq '.data.repository | to_entries[] | {number: .value.number, id: .value.id, title: .value.title}'
