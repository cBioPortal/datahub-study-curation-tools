set -e
set -o pipefail

test -n "$SYNAPSE_DOWNLOAD_PATH"
test -n "$SYN_ID"
test -n "$SYNAPSE_AUTH_TOKEN"

if [ -d $SYNAPSE_DOWNLOAD_PATH ]; then
    echo 'Removing existing directory..'
    rm -rf $SYNAPSE_DOWNLOAD_PATH || handle_error "Failed to remove directory $SYNAPSE_DOWNLOAD_PATH"
fi

echo 'Downloading data from Synapse..'
synapse -p $SYNAPSE_AUTH_TOKEN get -r $SYN_ID --downloadLocation $SYNAPSE_DOWNLOAD_PATH --followLink || handle_error "Failed to download data from Synapse"
echo -e '\\nFiles are downloaded to: $SYNAPSE_DOWNLOAD_PATH\\n'
