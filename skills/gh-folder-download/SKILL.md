---
name: gh-folder-download
description: Download a specific folder from a GitHub repository without cloning the entire repo. This skill should be used when the user asks to download a folder from GitHub, fetch docs from a repo subfolder, or get files from a specific GitHub path. Trigger phrases include "download this GitHub folder", "get the docs from this repo", "fetch files from GitHub path".
---

# GitHub Folder Download

Download a specific subfolder from any GitHub repository using the GitHub API zipball endpoint. Avoids cloning the entire repository.

## Usage

Run the bundled script:

```bash
python scripts/download_gh_folder.py <github_url> <output_dir>
```

### Parameters

| Parameter    | Description                                                              |
| ------------ | ------------------------------------------------------------------------ |
| `github_url` | GitHub folder URL in format `https://github.com/owner/repo/tree/ref/path` |
| `output_dir` | Local directory to save the downloaded files                             |

### Examples

```bash
# Download docs folder from main branch
python scripts/download_gh_folder.py \
  https://github.com/statelyai/docs/tree/main/content/docs \
  ./docs/stately

# Download from specific commit
python scripts/download_gh_folder.py \
  https://github.com/owner/repo/tree/abc123def/src/components \
  ./local-components
```

## How It Works

1. Parse the GitHub URL to extract owner, repo, ref (branch/tag/commit), and folder path
2. Download the repository archive via GitHub API: `GET /repos/{owner}/{repo}/zipball/{ref}`
3. Extract the archive to a temporary directory
4. Copy only the requested folder to the output directory
5. Clean up temporary files

## Post-Download Steps

After downloading, consider adding the folder to `.gitignore` if the files should not be committed:

```bash
echo "path/to/downloaded/" >> .gitignore
```
