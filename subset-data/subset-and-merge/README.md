### Usage

This tool is intended to subset and merge the studies. The files in the source directories must be in cBioPortal's standard [file formats](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats).

#### Running the tool

The script takes in either a list of sample IDs to subset on or a list of sample IDs to exclude from the source directories. The script can be run as,

```
python2.7 subset_and_merge_wrapper.py --subset [/path/to/subset] --output-directory [/path/to/output] --study-id [study id] --cancer-type [cancer type] --merge-clinical [true/false] --exclude-supplemental-data [true/false] --excluded-samples [/path/to/exclude_list] <path/to/study path/to/study ...>'
```

**Options**
```
-s | --subset : Path to the file with the list of Sample IDs to subset from source directories.
-e | --excluded-samples : Path to the file with the list of Sample IDs to exclude from source directories. `-e` is mutually exclusive to `-s`. Only one of the option can be passed.
-d | --output-directory : Path to a directory where the script writes the subset/merged files to. If the path to the directory does not exist, it gets created.
-i | --study-id : The study ID of the output directory.
-t | --cancer-type : Cancer type of the output directory.
-m | --merge-clinical : Merge clinical files (true or false).
-x | --exclude-supplemental-data : Exclude supplemental data (true or false).
```

**Example:**
```
python2.7 subset_and_merge_wrapper.py -s subset_samples.txt -d output/directory -i brca_msk_2022 -t brca -m true -x false dmp-2022/msk_solid_heme private/brca_msk_2019
```


**Note**
- Passing one source directory subsets the data and passing multiple directories subsets and merges the data.  

