### Usage

This script is tailored for converting GENIE consortium [fusion data](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#fusion-data) from cBioPortal version 4 and below to the [new structural variant data](https://docs.cbioportal.org/file-formats/#structural-variant-data) format used in cBioPortal version 5. 
The GENIE dataset features unique formatting and data conventions from various centers. The script identifies the genes at Site1 and Site2 based on their positions in the "Event_Info" column and adjusts field names to align with the SV format. 
It also handles duplicate entries in the fusion data by considering both orientations of Site1 and Site2 genes, ensuring that all gene interactions are represented in the patient view.

The tool outputs the fusion data in the cBioPortal's [SV file format](https://docs.cbioportal.org/file-formats/#structural-variant-data).

#### Running the tool

The tool can be run with the following command:

```
python3 fusion_to_sv_converter_genie.py [-h] --fusion_file <path/to/data_fusions.txt> --sv_file <path/to/data_sv.txt>
```

#### Command Line
```
python3 fusion_to_sv_converter_genie.py --help
```

```
usage: fusion_to_sv_converter_genie.py [-h] -f FUSION_FILE -s SV_FILE

optional arguments:
  -h, --help            show this help message and exit
  -f FUSION_FILE, --fusion_file FUSION_FILE
                        Path to the fusion file
  -s SV_FILE, --sv_file SV_FILE
                        Path to save the structural variant file
```

#### NOTE:
-The source fusion file must be in cBioPortal's old [fusion file format](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#fusion-data) with at least a minimum of `Hugo_Symbol`, `Entrez_Gene_Id`, `Tumor_Sample_Barcode` and `Fusion` fields.

- In case of duplicate entries (records that differ by values other than in the `Hugo_Symbol`, `Entrez_Gene_Id`, `Tumor_Sample_Barcode` and `Fusion` fields), the script picks the last occuring value.
