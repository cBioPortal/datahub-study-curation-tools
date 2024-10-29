#!/bin/bash
set -euxo pipefail

test -n "$REPOS_DIR"
test -n "$PUSH_TO_REPO"

genie_path=$REPOS_DIR/genie

echo "Pushing genie repo at $genie_path"
cd "$genie_path"
# https://stackoverflow.com/a/71904131/4077294
git config --global --add safe.directory "$genie_path"

# `git commit` will exit 1 if there is nothing to commit, ignore the error in that case
git commit -m "Update genie data from Synapse" || true
if [ "$PUSH_TO_REPO" = 'yes' ]; then
    git push origin
else
    # https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/bash.html#skipping
    exit 99
fi