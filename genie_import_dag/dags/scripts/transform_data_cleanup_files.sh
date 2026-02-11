set -e
set -o pipefail

STUDY_PATH="{{ ti.xcom_pull(task_ids='identify_release_create_study_dir') }}"

if [ -z "$STUDY_PATH" ]; then
    echo "Error: STUDY_PATH is empty or unset." >&2
    exit 1
fi

if [ ! -d "$STUDY_PATH" ]; then
    echo "Error: Study directory $STUDY_PATH does not exist." >&2
    exit 1
fi

files_to_remove=("*.pdf" "*.csv" "*.html" "*.bed" "assay_information.txt" "genomic_information.txt" "SYNAPSE_METADATA_MANIFEST.tsv" "case_lists/SYNAPSE_METADATA_MANIFEST.tsv")

for pattern in "${files_to_remove[@]}"; do
    for dir in "$STUDY_PATH" "$STUDY_PATH/case_lists"; do
        for file in "$dir"/$pattern; do
            if [ -e "$file" ]; then
                rm "$file"
                echo -e "Removed $(basename "$file") from $dir"
            fi
        done
    done
done

echo "$STUDY_PATH"
