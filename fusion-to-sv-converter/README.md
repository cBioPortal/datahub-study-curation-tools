### Usage

This tool is intended to convert the Fusion files to the Structural Variant data format.

The source fusion file must be in cBioPortal's standard [fusion file format](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#fusion-data) with at least a minimum of `Hugo_Symbol`, `Entrez_Gene_Id`, `Tumor_Sample_Barcode` and `Fusion` fields.

The tool outputs the fusion data in the cBioPortals [SV file format](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#structural-variant-data).

#### Running the tool

The tool can be run with the following command:

```
python3 fusion_to_sv_converter.py [-h] --fusion_file <path/to/data_fusions.txt> --sv_file <path/to/data_sv.txt>
```

#### Command Line
```
python fusion_to_sv_converter.py --help
```

```
usage: fusion_to_sv_converter.py [-h] -f FUSION_FILE -s SV_FILE [-repo [SOURCE_REPO]]

optional arguments:
  -h, --help            show this help message and exit
  -f FUSION_FILE, --fusion_file FUSION_FILE
                        Path to the fusion file
  -s SV_FILE, --sv_file SV_FILE
                        Path to save the structural variant file
```

#### NOTE:
- In case of duplicate entries (records that differ by values other than in the `Hugo_Symbol`, `Entrez_Gene_Id`, `Tumor_Sample_Barcode` and `Fusion` fields), the script picks the last occuring value.
