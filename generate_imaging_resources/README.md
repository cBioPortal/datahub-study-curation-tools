# Generate TCGA Imaging Resources Script

This script downloads TCGA imaging data from the NCI Imaging Data Commons (IDC) and generates cBioPortal-compatible resource files.

## Purpose

Downloads TCGA imaging metadata from IDC and links TCGA patients to their imaging studies (CT, MRI, PET scans, H&E slides) by creating resource files that enable direct viewing through OHIF and SLIM viewers within cBioPortal.

## Prerequisites

### Dependencies
```bash
pip install pandas numpy idc-index
```

### Input Files Required

**TCGA Pan Cancer Atlas 2018 studies**: Directory containing study folders with `data_clinical_patient.txt` files

## Usage

1. Update the `dh_files_path` variable in the script to point to your datahub public directory:
   ```python
   dh_files_path = "/path/to/your/datahub/public"
   ```

2. Run the script:
   ```bash
   python generate_imaging_resources.py
   ```

The script will:
1. Download TCGA imaging data from IDC and save to `idc_tcga.txt`
2. Process the data and generate resource files for each TCGA Pan-Cancer Atlas 2018 study

## Output Files

For each TCGA Pan-Cancer Atlas 2018 study, the script generates two files:

1. **`data_resource_patient.txt`**: Links patients to their imaging studies
   - Columns: `PATIENT_ID`, `RESOURCE_ID`, `URL`
   
2. **`data_resource_definition.txt`**: Defines the resource types available in the study
   - Columns: `RESOURCE_ID`, `DISPLAY_NAME`, `RESOURCE_TYPE`, `DESCRIPTION`, `OPEN_BY_DEFAULT`, `PRIORITY`

## Resource Mappings

| Modality Code | Resource ID | Display Name | Viewer |
|---------------|-------------|--------------|---------|
| CR | IDC_OHIF_CR | Computed Radiography | OHIF |
| CT | IDC_OHIF_CT | CT Scan | OHIF |
| DX | IDC_OHIF_DX | Digital Radiography | OHIF |
| MG | IDC_OHIF_MG | Mammography | OHIF |
| MR | IDC_OHIF_MR | Magnetic Resonance | OHIF |
| NM | IDC_OHIF_NM | Nuclear Medicine | OHIF |
| PT | IDC_OHIF_PT | PET Scan | OHIF |
| SM | IDC_SLIM | H&E Slide | SLIM |

## Viewer URLs

- **OHIF**: `https://viewer.imaging.datacommons.cancer.gov/viewer/{StudyInstanceUID}`
- **SLIM**: `https://viewer.imaging.datacommons.cancer.gov/slim/studies/{StudyInstanceUID}`

## Notes

- Only processes patients already present in clinical data files
- Annotation (ANN), Segmentation (SEG), and Structured Reports (SR) are excluded as standalone resources since they're automatically loaded with their parent imaging studies in OHIF
