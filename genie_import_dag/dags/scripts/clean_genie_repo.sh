#!/bin/bash
set -euxo pipefail

test -n "$REPOS_DIR"
test -n "$PUSH_TO_REPO"

# If we aren't pushing to the remote repo, we want to
# examine the data locally and git clean manually.
# Exit the script without cleaning the git repo.
if [ "$PUSH_TO_REPO" != 'yes' ]; then
    exit 99
fi

genie_path=$REPOS_DIR/genie

echo "Cleaning datahub repo at $genie_path"
cd "$genie_path"
git config --global --add safe.directory "$genie_path"

current_github_branch=$(git rev-parse --abbrev-ref HEAD)

git checkout -- .
git clean -fd
git reset --hard origin/$current_github_branch
git lfs prune # Delete old, unreferenced LFS files from local storage