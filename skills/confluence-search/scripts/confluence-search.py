#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "atlassian-python-api>=3.41.0",
# ]
# ///
"""
Search Confluence and output JSON.

COMMANDS
    QUERY                   Text search across all pages
    -p, --page ID           Fetch a single page by ID
    --children ID           List child pages of a page/folder
    --list-spaces           List all available spaces
    --cql "QUERY"           Execute raw CQL (Confluence Query Language)

OPTIONS
    -s, --space KEY         Limit search to a space (e.g., TECH, SYS)
    -l, --limit N           Max results (default: 10)
    -c, --content           Include page body in search results
    --raw                   Output raw HTML instead of plain text

OUTPUT FIELDS
    Search results:   id, title, space, url, modified, [body], [parent_id], [truncated]
    Single page:      id, title, space, version, body, [parent_id], [parent_title], [truncated], [total_length]
    Child pages:      id, title, parent_id, version, url
    Spaces:           key, name, type, description

EXAMPLES
    # Basic search
    confluence-search.py "deployment guide"

    # Search in specific space
    confluence-search.py "kubernetes" -s SYS -l 20

    # Fetch page with parent info
    confluence-search.py -p 12345678

    # List children of a folder
    confluence-search.py --children 12345678

    # CQL query for descendants
    confluence-search.py --cql "ancestor=12345678 AND type=page"

    # Compose with jq
    confluence-search.py "datadog" | jq '.[].title'
    confluence-search.py --list-spaces | jq '.[] | select(.type == "global") | .key'

ENVIRONMENT
    ATLASSIAN_EMAIL       Your Atlassian account email
    ATLASSIAN_API_TOKEN   API token from https://id.atlassian.com/manage-profile/security/api-tokens
    ATLASSIAN_BASE_URL    Instance URL (e.g., https://yourorg.atlassian.net)
"""

import argparse
import html
import json
import os
import re
import sys
from typing import Any

from atlassian import Confluence

# Maximum body length before truncation (characters)
MAX_BODY_LENGTH = 50000


def _print_setup_guide(missing: list[str]) -> None:
    """Print setup instructions to stderr."""
    sys.stderr.write(f"Error: Missing environment variables: {', '.join(missing)}\n\n")
    sys.stderr.write("Setup:\n")
    sys.stderr.write("  1. Get API token: https://id.atlassian.com/manage-profile/security/api-tokens\n")
    sys.stderr.write("  2. Add to ~/.secrets (or ~/.bashrc/.zshrc):\n\n")
    sys.stderr.write('     export ATLASSIAN_EMAIL="you@company.com"\n')
    sys.stderr.write('     export ATLASSIAN_API_TOKEN="your-api-token"\n')
    sys.stderr.write('     export ATLASSIAN_BASE_URL="https://yourorg.atlassian.net"\n\n')
    sys.stderr.write("  3. Source it: source ~/.secrets\n")


def get_client() -> Confluence:
    """Create Confluence client from environment."""
    email = os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("ATLASSIAN_API_TOKEN")
    url = os.environ.get("ATLASSIAN_BASE_URL")
    if not all([email, token, url]):
        missing = [
            k
            for k, v in [
                ("ATLASSIAN_EMAIL", email),
                ("ATLASSIAN_API_TOKEN", token),
                ("ATLASSIAN_BASE_URL", url),
            ]
            if not v
        ]
        _print_setup_guide(missing)
        sys.exit(1)
    return Confluence(url=url, username=email, password=token, cloud=True)


def strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def truncate_body(body: str) -> tuple[str, bool]:
    """Truncate body if too long, return (body, was_truncated)."""
    if len(body) > MAX_BODY_LENGTH:
        return body[:MAX_BODY_LENGTH] + "\n\n... [truncated]", True
    return body, False


def search(query: str, space: str | None, limit: int, content: bool) -> list[dict[str, Any]]:
    """Search Confluence, return list of results."""
    client = get_client()
    cql = f"text ~ '{query}'"
    if space:
        cql += f" AND space = '{space}'"
    results = client.cql(cql, limit=limit).get("results", [])
    out = []
    for r in results:
        item: dict[str, Any] = {
            "id": r.get("content", {}).get("id"),
            "title": r.get("title"),
            "space": r.get("resultGlobalContainer", {}).get("title"),
            "url": r.get("url"),
            "modified": r.get("friendlyLastModified"),
        }
        if content and item["id"]:
            page = client.get_page_by_id(item["id"], expand="body.storage,ancestors")
            body_html = page.get("body", {}).get("storage", {}).get("value", "")
            body_text = strip_html(body_html)
            body_text, truncated = truncate_body(body_text)
            item["body"] = body_text
            if truncated:
                item["truncated"] = True
            # Add parent_id from ancestors
            ancestors = page.get("ancestors", [])
            if ancestors:
                item["parent_id"] = ancestors[-1].get("id")
        out.append(item)
    return out


def search_cql(cql: str, limit: int, content: bool) -> list[dict[str, Any]]:
    """Execute raw CQL query."""
    client = get_client()
    results = client.cql(cql, limit=limit).get("results", [])
    out = []
    for r in results:
        item: dict[str, Any] = {
            "id": r.get("content", {}).get("id"),
            "title": r.get("title"),
            "space": r.get("resultGlobalContainer", {}).get("title"),
            "url": r.get("url"),
            "modified": r.get("friendlyLastModified"),
        }
        if content and item["id"]:
            page = client.get_page_by_id(item["id"], expand="body.storage")
            body_html = page.get("body", {}).get("storage", {}).get("value", "")
            body_text = strip_html(body_html)
            body_text, truncated = truncate_body(body_text)
            item["body"] = body_text
            if truncated:
                item["truncated"] = True
        out.append(item)
    return out


def get_page(page_id: str, raw: bool) -> dict[str, Any]:
    """Fetch a single page by ID."""
    client = get_client()
    page = client.get_page_by_id(page_id, expand="body.storage,version,space,ancestors")
    body_html = page.get("body", {}).get("storage", {}).get("value", "")

    if raw:
        body = body_html
    else:
        body = strip_html(body_html)

    body, truncated = truncate_body(body)

    result: dict[str, Any] = {
        "id": page.get("id"),
        "title": page.get("title"),
        "space": page.get("space", {}).get("name"),
        "version": page.get("version", {}).get("number"),
        "body": body,
    }

    if truncated:
        result["truncated"] = True
        result["total_length"] = len(body_html) if raw else len(strip_html(body_html))

    # Add parent info from ancestors
    ancestors = page.get("ancestors", [])
    if ancestors:
        result["parent_id"] = ancestors[-1].get("id")
        result["parent_title"] = ancestors[-1].get("title")

    return result


def get_child_pages(page_id: str, limit: int) -> list[dict[str, Any]]:
    """Get child pages of a given page."""
    client = get_client()
    children = client.get_page_child_by_type(page_id, type="page", limit=limit, expand="version")
    out = []
    for child in children:
        out.append({
            "id": child.get("id"),
            "title": child.get("title"),
            "parent_id": page_id,
            "version": child.get("version", {}).get("number"),
            "url": child.get("_links", {}).get("webui", ""),
        })
    return out


def list_spaces(limit: int) -> list[dict[str, Any]]:
    """List all available spaces."""
    client = get_client()
    response = client.get_all_spaces(limit=limit, expand="description.plain")
    spaces = response.get("results", []) if isinstance(response, dict) else response
    out = []
    for space in spaces:
        out.append({
            "key": space.get("key"),
            "name": space.get("name"),
            "type": space.get("type"),
            "description": space.get("description", {}).get("plain", {}).get("value", ""),
        })
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Search Confluence and output JSON.",
        epilog="Run with no arguments to see full documentation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("query", nargs="?", metavar="QUERY", help="text search across all pages")
    p.add_argument("-s", "--space", metavar="KEY", help="limit search to space key (e.g., TECH)")
    p.add_argument("-l", "--limit", type=int, default=10, metavar="N", help="max results (default: 10)")
    p.add_argument("-c", "--content", action="store_true", help="include page body in search results")
    p.add_argument("-p", "--page", metavar="ID", help="fetch single page by ID")
    p.add_argument("--raw", action="store_true", help="output raw HTML instead of plain text")
    p.add_argument("--children", metavar="ID", help="list child pages of a page/folder")
    p.add_argument("--list-spaces", action="store_true", help="list all available spaces")
    p.add_argument("--cql", metavar="QUERY", help="execute raw CQL query")
    args = p.parse_args()

    if args.list_spaces:
        result = list_spaces(args.limit)
    elif args.children:
        result = get_child_pages(args.children, args.limit)
    elif args.page:
        result = get_page(args.page, args.raw)
    elif args.cql:
        result = search_cql(args.cql, args.limit, args.content)
    elif args.query:
        result = search(args.query, args.space, args.limit, args.content)
    else:
        # Show full documentation when no arguments provided
        print(__doc__)
        sys.exit(0)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
