set -e
set -o pipefail

test -n "$SYNAPSE_DOWNLOAD_PATH"
test -n "$REPOS_DIR"

function handle_error {
    echo "$1" >&2
    exit 1
}

if [ ! -f "$SYNAPSE_DOWNLOAD_PATH/meta_study.txt" ]; then
    handle_error "Error: meta_study.txt not found in $SYNAPSE_DOWNLOAD_PATH"
fi

study_identifier=$(grep "cancer_study_identifier" $SYNAPSE_DOWNLOAD_PATH/meta_study.txt | awk -F ": " '{print $2}')
if [ -z "$study_identifier" ]; then
    handle_error "Error: Study identifier not found or empty in meta_study.txt"
fi
echo "Study Identifier: $study_identifier"

REPO_NAME=genie
GENIE_STUDY_PATH="$REPOS_DIR/$REPO_NAME/$study_identifier"

echo -e "Moving files to $GENIE_STUDY_PATH...\n"
cp -r $SYNAPSE_DOWNLOAD_PATH/* "$GENIE_STUDY_PATH" || handle_error "Failed to move files to $GENIE_STUDY_PATH"
echo "$GENIE_STUDY_PATH"
