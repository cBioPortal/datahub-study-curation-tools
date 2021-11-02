### Usage
Add `somatic status` column (value: `Matched` or `Unmatched`) to clinical sample file

### Command Line

usage: addSomaticStatusCol.py [-h] -i INPUT_CLINICAL_FILE_NAME
                              [-l INPUT_SAMPLE_STATUS_LIST]
                              [-s STATUS_FOR_ALL_SAMPLES] -o OUTPUT_FILE_NAME

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_CLINICAL_FILE_NAME, --input-clinical-file-name INPUT_CLINICAL_FILE_NAME
                        Original Clinical File
  -l INPUT_SAMPLE_STATUS_LIST, --input-sample-status-list INPUT_SAMPLE_STATUS_LIST
                        List of Sample vs. Matched Normal Status (Optional)
  -s STATUS_FOR_ALL_SAMPLES, --overall-status STATUS_FOR_ALL_SAMPLES
                        Unified Status for all samples (Optional)
  -o OUTPUT_FILE_NAME, --onput-file-name OUTPUT_FILE_NAME
                        Output File

* for `-s`: `1` is the `Matched`, `0` is for `Unmatched`               

### Example

For mixed status for sample set
```
python path/to/addSomaticStatusCol.py -i path/to/data_clincial_sample.txt -l path/to/sample_status_list.txt
```

For unified status for all samples
```
python path/to/addSomaticStatusCol.py -i path/to/data_clincial_sample.txt -s 1
```

### Notes
Have to fill in either `-l` or `-s` option. Can not do both or neither.