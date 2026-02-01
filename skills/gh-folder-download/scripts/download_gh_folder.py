#!/usr/bin/env python3
"""Download a specific folder from a GitHub repository.

Usage:
    python download_gh_folder.py <github_url> <output_dir>

Examples:
    python download_gh_folder.py https://github.com/owner/repo/tree/main/docs ./local-docs
    python download_gh_folder.py https://github.com/owner/repo/tree/abc123/src/lib ./lib
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def parse_github_url(url: str) -> tuple[str, str, str, str]:
    """Parse GitHub URL to extract owner, repo, ref, and path.

    Returns:
        Tuple of (owner, repo, ref, path)
    """
    # Pattern: https://github.com/owner/repo/tree/ref/path/to/folder
    pattern = r"github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(
            f"Invalid GitHub folder URL: {url}\n"
            "Expected format: https://github.com/owner/repo/tree/branch/path/to/folder"
        )

    return match.group(1), match.group(2), match.group(3), match.group(4)


def download_and_extract(owner: str, repo: str, ref: str, folder_path: str, output_dir: Path) -> None:
    """Download repo zipball and extract the specified folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_path = tmpdir / "repo.zip"

        # Download zipball from GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}"
        print(f"Downloading from {api_url}...")

        result = subprocess.run(
            ["curl", "-L", "-o", str(zip_path), api_url],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to download: {result.stderr}")

        if not zip_path.exists() or zip_path.stat().st_size == 0:
            raise RuntimeError("Download failed - empty or missing file")

        # Extract zip
        extract_dir = tmpdir / "extracted"
        extract_dir.mkdir()

        print("Extracting archive...")
        result = subprocess.run(
            ["unzip", "-q", str(zip_path), "-d", str(extract_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract: {result.stderr}")

        # Find the extracted repo folder (format: owner-repo-commitsha)
        repo_folders = list(extract_dir.iterdir())
        if not repo_folders:
            raise RuntimeError("No folder found in extracted archive")

        repo_folder = repo_folders[0]
        source_folder = repo_folder / folder_path

        if not source_folder.exists():
            raise RuntimeError(
                f"Folder '{folder_path}' not found in repository.\n"
                f"Available top-level folders: {[f.name for f in repo_folder.iterdir() if f.is_dir()]}"
            )

        # Copy to output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Copying to {output_dir}...")
        for item in source_folder.iterdir():
            dest = output_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Count items
        item_count = sum(1 for _ in output_dir.rglob("*"))
        print(f"Successfully downloaded {item_count} items to {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download a specific folder from a GitHub repository"
    )
    parser.add_argument(
        "url",
        help="GitHub folder URL (e.g., https://github.com/owner/repo/tree/main/docs)",
    )
    parser.add_argument(
        "output",
        help="Output directory path",
    )

    args = parser.parse_args()

    try:
        owner, repo, ref, folder_path = parse_github_url(args.url)
        print(f"Repository: {owner}/{repo}")
        print(f"Ref: {ref}")
        print(f"Folder: {folder_path}")

        download_and_extract(owner, repo, ref, folder_path, Path(args.output))
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
