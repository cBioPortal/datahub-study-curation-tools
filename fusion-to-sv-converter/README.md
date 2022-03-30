### Usage

This tool is intended to convert the Fusion files to the Structural variant format.

The source fusion file must be in cBioPortal's standard [fusion file format](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#fusion-data) with at least a minimum of `Hugo_Symbol`, `Entrez_Gene_Id`, `Tumor_Sample_Barcode` and `Fusion` fields.
The tool outputs the fusion data in the cBioPortals [SV file format](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats#structural-variant-data)

#### Running the tool

The tool can be run with the following command:

```
python3 fusion_to_sv_converter.py [-h] --fusion_file <path/to/data_fusions.txt> --sv_file <path/to/data_sv.txt> --source_repo repo/name
```

If the `--source_repo` option is not passed, the repo-name is defaulted to `cmo-argos`.

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
  -repo [SOURCE_REPO], --source_repo [SOURCE_REPO]
                        Defaulted to cmo-argos. Enter the source repo of the fusion file otherwise.
```