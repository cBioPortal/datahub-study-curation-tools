#!/bin/bash
set -euxo pipefail

test -n "$REPOS_DIR"
    
# Configure Git LFS not to download all data files right away
git lfs install --skip-repo --skip-smudge

repo_name=genie
repo_url=git@github.com:knowledgesystems/genie.git
branch=master

# Check if repo already exists
# If it does, we will still smudge it (aka download the actual contents of the LFS files we need)
cd "$REPOS_DIR"
if [ -d "${repo_name}" ] ; then
    echo "${repo_name} already exists"
    exit 99
fi

# Git clone
echo "Cloning LFS repo ${repo_url} to ${REPOS_DIR}/${repo_name}"
git clone $repo_url -b $branch --progress