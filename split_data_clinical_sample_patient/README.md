### Usage
Split `data_clinical.txt` into `data_clinical_sample.txt` and `data_clinical_patient.txt`

### Command Line
```
split_data_clinical_attributes.py --clinical-file path/to/clinical/file
```

### Example
```
cd path/to/study
python split_data_clinical_attributes.py --clinical-file data_clinical.txt
rm data_clinical.txt
```

### Notes
path of `clinical_attributes_metadata.txt` needs to be defined in line #10
`clinical_attributes_metadata.txt` needs to be synced with corresponding `topbraid` clinical data dictionary project