#!/bin/bash
set -euxo pipefail

test -n "$REPOS_DIR"

genie_path=$REPOS_DIR/genie

echo "Fetching genie repo at $genie_path"
cd "$genie_path"
# https://stackoverflow.com/a/71904131/4077294
git config --global --add safe.directory "$genie_path"

# Install LFS hooks into repo
git lfs install --local --skip-smudge

# Fetch latest updates for the current branch
current_github_branch=$(git rev-parse --abbrev-ref HEAD)
git fetch
git reset --hard origin/$current_github_branch
git pull origin $current_github_branch

# Smudge the data files for study folders
echo "Pulling Genie study data"
git lfs pull