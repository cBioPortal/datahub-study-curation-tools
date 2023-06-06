#!/bin/bash

# Copyright (c) 2023 Memorial Sloan Kettering Cancer Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# GLOBALS
GENOME_NEXUS_ANNOTATOR_JAR=annotator.jar
GENOME_NEXUS_ANNOTATOR_ISOFORM="mskcc"
GENOME_NEXUS_ANNOTATOR_POST_SIZE=1000

# verify python3 installation
command -v python3 >/dev/null 2>&1 || { echo "python3 is required to run this program - aborting..." >&2; exit 1; }

function usage {
    echo "automate_curation.sh"
    echo -e "\t-s | --subset-identifiers            provide a list of patient/sample identifiers to either select or exclude from [REQUIRED]"
    echo -e "\t-i | --input-directories             A list of input data directories to subset the data from, separated by commas [REQUIRED]"
    echo -e "\t-e | --exclude-identifiers           Entering 'True' for this setting will exclude any samples included in the provided list from the subset. The default is 'False' [OPTIONAL]"
}

# parse input arguments
for i in "$@"; do
case $i in
    -s=*|--subset-identifiers=*)
    SUBSET_IDENTIFIERS="${i#*=}"
    echo -e "\tSUBSET_IDENTIFIERS=${SUBSET_IDENTIFIERS}"
    shift
    ;;
    -i=*|--input-directories=*)
    INPUT_DATA_DIRECTORIES="${i#*=}"
    echo -e "\tINPUT_DATA_DIRECTORIES=${INPUT_DATA_DIRECTORIES}"
    shift
    ;;
    -e=*|--exclude-identifiers=*)
    EXCLUDE_IDENTIFIERS="${i#*=}"
    echo -e "\tEXCLUDE_IDENTIFIERS=${EXCLUDE_IDENTIFIERS}"
    shift
    ;;
    *)
    echo "Invalid option: $1"
    exit 1
    ;;
esac
done

if [[ -z "${SUBSET_IDENTIFIERS}" || -z "${INPUT_DATA_DIRECTORIES}" ]]; then
    usage
    exit 1
fi

# Subset or exclude samples from the dataset based on the provided list.
if [[ -z "${EXCLUDE_IDENTIFIERS}" || ${EXCLUDE_IDENTIFIERS} = 'False' ]]; then
    echo -e "\nFiltering and combining data from $INPUT_DATA_DIRECTORIES"
    outpath=$(python3 merge.py --subset-samples ${SUBSET_IDENTIFIERS} --input-directory ${INPUT_DATA_DIRECTORIES})
    echo -e "\nFilter and merge complete!"
elif [[ ${EXCLUDE_IDENTIFIERS} = 'True' ]]; then
    echo -e "\nFiltering and combining data from $INPUT_DATA_DIRECTORIES"
    outpath=$(python3 merge.py --excluded-samples ${SUBSET_IDENTIFIERS} --input-directory ${INPUT_DATA_DIRECTORIES})
    echo -e "\nFilter and merge complete!"
else
    echo -e "\nThe '--exclude-identifiers' parameter only accepts either 'True' or 'False' as values."
fi

IFS=':' read -ra arr <<< "$outpath"
path="${arr[1]#"${arr[1]%%[![:space:]]*}"}"
out_directory=$(basename "$path")

declare -a files
while IFS= read -r file; do
  files+=("$file")
done < <(find "$out_directory" -type f -iname "data_mutations*")

for MAF_FILE in "${files[@]}"; do
    ANNOTATED_MAF=$MAF_FILE."_ann"
    if  [ -f $MAF_FILE ]; then
    	# Remove GERMLINE variants from the MAF
    	echo -e "\nRemoving GERMLINE variants.."
    	grep -v 'GERMLINE' $MAF_FILE > $MAF_FILE.tmp
    	mv $MAF_FILE.tmp $MAF_FILE

    	# Annotate MAF
    	echo -e "\nAnnotating MAF: $MAF_FILE"
    	python3 annotate_maf.py --input-maf ${MAF_FILE} --output-maf ${ANNOTATED_MAF} --annotator-jar ${GENOME_NEXUS_ANNOTATOR_JAR} --isoform ${GENOME_NEXUS_ANNOTATOR_ISOFORM} --post-size ${GENOME_NEXUS_ANNOTATOR_POST_SIZE}
    	if [ -f $ANNOTATED_MAF ]; then
        	mv $ANNOTATED_MAF $MAF_FILE
        	echo "Annotation complete!"
    	fi
	else
    	echo -e "\n$MAF_FILE does not exist. Skipping annotation.."
	fi
done

# Generate missing meta files
echo -e "\nGenerating missing meta files.."
python3 generate_missing_metafiles.py --directory ${out_directory} --study_id ${out_directory}

# Generate missing case lists
echo -e "\nGenerating missing case lists.."
python3 generate_case_lists.py --case-list-config-file 'config_files/case_list_conf.txt' --case-list-dir ${out_directory}'/case_lists' --study-dir ${out_directory} --study-id ${out_directory}

# Add Cancer Type and Cancer Type Detailed if Oncotree Code column exists
echo -e "\nAdding Cancer Type and Cancer Type Detailed columns to Clinical.."
python3 generate_ct_ctd.py --clinical-file  ${out_directory}'/data_clinical_sample.txt' --oncotree-url 'http://oncotree.mskcc.org/' --oncotree-version 'oncotree_candidate_release'

# TODO:
# Generate TMB Scores - requires a repository of gene panels (for internal we don't have these) with the number of profiled coding base pairs calculated.

# Final checks - check for any extra meta, case lists files were copied over and remove
echo -e "\nValidating the data generated.."
python3 end_validation.py --input-directory  ${out_directory}

echo -e "\nThe dataset is written to the folder: ${out_directory}\n"
