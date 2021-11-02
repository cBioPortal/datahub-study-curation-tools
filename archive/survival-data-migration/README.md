### Survival Data Migration Tool

This tool is intended to convert the survival data from their custom vocabulary to `0 / 1` format. 

Example, the values `Living / Deceased` of Overall Survival Status (OS_STATUS) is converted to the new format `0:Living / 1:Deceased`

#### Command Line
```
  -h, --help            show this help message and exit
  -f CLINICALFILE, --clinicalFile CLINICALFILE
                        absolute path to the data file that needs to be migrated
  -v VOCABULARIESFILE, --vocabulariesFile VOCABULARIESFILE
                        absolute path to the custom vocabularies file to map
                        the value
  -o OVERRIDE, --override OVERRIDE
                        override the old file or not
  -n NEWFILE, --newFile NEWFILE
                        absolute path to save the new migrated file
  -a ADDITIONALVOCABULARIES, --additionalVocabularies ADDITIONALVOCABULARIES
                        additional vocabularies to map the value, example
                        format:
                        1:mapToOne_1,mapToOne2#0:mapToZero_1,mapToZero2
```

#### Usage
```
python survivalDataMigration.py [-h] -f CLINICALFILE -v VOCABULARIESFILE [-o OVERRIDE] [-n NEWFILE] [-a ADDITIONALVOCABULARIES]
```

The vocabularies file has a pre-defined mapping of values captured in our observation. Use the `--additionalVocabularies` option to pass new vocabularies in the format: `0:vocabulary1_mapping_to_0,vocabulary2_mapping_to_0#1:vocabulary1_mapping_to_1,vocabulary2_mapping_to_1`

Use the `--override` option to specify if `CLINICALFILE` should be overrided or not. It is set to `False` by default and the output is saved to a new file (`Migrated_CLINICALFILE`). Use the `--newFile` option to save the output to a filename of interest.

#### Example
```
python survivalDataMigration.py -f ~/data_clinical_patient.txt -v survivalStatusVocabularies.txt -o True
```   
OR
```
python survivalDataMigration.py -f ~/data_clinical_patient.txt -v survivalStatusVocabularies.txt -n ~/data_clinical_patient_migrated.txt -a 0:DiseaseFree#1:Recurred/Progressed
```