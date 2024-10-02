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

study_identifier=$(grep "cancer_study_identifier" $SYNAPSE_DOWNLOAD_PATH/meta_study.txt | awk -F ": " '{{print $2}}')
if [ -z "$study_identifier" ]; then
    handle_error "Error: Study identifier not found or empty in meta_study.txt"
fi
echo "Study Identifier: $study_identifier"

GENIE_STUDY_PATH="$REPOS_DIR/$study_identifier"
if [ -d "$GENIE_STUDY_PATH" ]; then
    echo 'Removing existing directory..'
    rm -rf "$GENIE_STUDY_PATH" || handle_error "Failed to remove directory $GENIE_STUDY_PATH"
fi

echo -e "Moving files to $GENIE_STUDY_PATH...\n"
mv $SYNAPSE_DOWNLOAD_PATH "$GENIE_STUDY_PATH" || handle_error "Failed to move files to $GENIE_STUDY_PATH"
echo "$GENIE_STUDY_PATH"
