### Usage

This tool is intended to subset a study based on the patient/sample IDs. The files in the source directory must be in cBioPortal's standard [file formats](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats).

#### Running the tool

The tool takes in either two files or two regexp's to subset on (for sample IDs, patient IDs). 

```
python3 subset-data.py [-h] [--sample-list <path/to/sampleIDs/file> --patient-list <path/to/patientIDs/file>] [--sample-regex 'sampleRegex' --patient-regex 'patientRegex'] --source-path <path/to/source/directory> --destination-path <path/to/destination/directory>
```

**Options**
```
 -s | --sample-list: This is the path to the file with sample IDs to subset on.
 -p | --patient-list: This is the path to the file with patient IDs to subset on.
 -sr | --sample-regex: This is the regex to subset the sample ID's.
 -pr | --patient-regex: This is the regex to subset the patient ID's.
 -path | --source-path: This is the path to the source directory to subset from. It can be either impact or any study directory.
 -dest | --destination-path: This is the destination directory to write the subsetted data to. 
```