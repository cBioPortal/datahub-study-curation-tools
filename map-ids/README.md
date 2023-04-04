### Usage

This tool is intended to rewrite all study files with new IDs based on the patient/sample ID maps. The files in the source directory must be in cBioPortal's standard [file formats](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats).

#### Running the tool

The tool takes in two files (for sample IDs, patient IDs) to map on. 

```
python map-ids.py [-h]
    -s <sample_id_map.csv> 
    --sample-from <original id column name in samples csv map>  
    --sample-to <new id column name in samples csv map> 
    -p patient_id_map.csv 
    --patient-from <original id column name in patients csv map>
    --patient-to <new id column name in samples csv map>
    -path <path/to/source/directory> 
    -dest <path/to/destination/directory> 
    [--drop-unknown True]

```

**Options**
```
 -s | --sample-map: This is the path to the csv file with sample IDs to map on.
--sample-from: name of the column with original IDs in the sample-ids-map csv file
--sample-to: name of the column with new IDs to be used in the sample-ids-map csv file

 -p | --patient-map: This is the path to the csv file with patient IDs to map on.
--sample-from: name of the column with original IDs in the patient-ids-map csv file
--sample-to: name of the column with new IDs to be used in the patient-ids-map csv file

 -path | --source-path: This is the path to the source directory to subset from. It can be either impact or any study directory.
 -dest | --destination-path: This is the destination directory to write the subsetted data to. 

 --drop-unknown: False by default will make script fail if it encounters an ID (sample or patient) for which there's no corresponding map (sample or patient) entry. If set to True - will silently ignore / discard that entry and continue.

```