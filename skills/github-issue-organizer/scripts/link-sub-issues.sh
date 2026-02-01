#!/bin/bash
# Link multiple issues as sub-issues to a parent
# Usage: ./link-sub-issues.sh PARENT_NODE_ID "CHILD_ID1 CHILD_ID2 CHILD_ID3"

set -euo pipefail

PARENT_ID="${1:?Parent node ID required}"
CHILD_IDS="${2:?Child node IDs required (space-separated string)}"

# Build mutation with aliases for each sub-issue
mutation="mutation {"

index=1
for child_id in $CHILD_IDS; do
    mutation+="link_${index}: addSubIssue(input: {issueId: \"$PARENT_ID\", subIssueId: \"$child_id\"}) { "
    mutation+="issue { number title } "
    mutation+="} "
    ((index++))
done

mutation+="}"

# Execute mutation
echo "Linking ${index} sub-issues to parent..."
gh api graphql -f query="$mutation"
echo "Done!"
