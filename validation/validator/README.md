# Introduction

This is a standalone version of cBioPortal data validator. It validates one or multiple studies formatted according to the [cBioPortal data formats](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats), and outputs reports in both plain text and HTML formats.

# Requirements

### Python3
Make sure `python3.x` is installed. Official information can be found at [python.org](https://www.python.org/downloads/)

### yaml
```
python3 -m pip install pyyaml
```

### jinja2
```
python3 -m pip install jinja2
```

# Usage

```
python3 validateStudies.py -d path/to/root/directory -l study_id -u cbioportal_server -html path/to/report/dir
```

```
validateStudies.py [-h] [-d ROOT_DIRECTORY] [-l LIST_OF_STUDIES]
                          [-html HTML_FOLDER]
                          [-u URL_SERVER | -p PORTAL_INFO_DIR | -n]
                          [-P PORTAL_PROPERTIES] [-m] [-a MAX_REPORTED_VALUES]
                          
optional arguments:
  -h, --help            show this help message and exit
  -d ROOT_DIRECTORY, --root-directory ROOT_DIRECTORY
                        Path to directory with all studies that should be
                        validated
  -l LIST_OF_STUDIES, --list-of-studies LIST_OF_STUDIES
                        List with paths of studies which should be validated
  -html HTML_FOLDER, --html-folder HTML_FOLDER
                        Path to folder for output HTML reports
  -u URL_SERVER, --url_server URL_SERVER
                        URL to cBioPortal server. You can set this if your URL
                        is not http://localhost:8080
  -p PORTAL_INFO_DIR, --portal_info_dir PORTAL_INFO_DIR
                        Path to a directory of cBioPortal info files to be
                        used instead of contacting a server
  -n, --no_portal_checks
                        Skip tests requiring information from the cBioPortal
                        installation
  -P PORTAL_PROPERTIES, --portal_properties PORTAL_PROPERTIES
                        portal.properties file path (default: assumed hg19)
  -m, --strict_maf_checks
                        Option to enable strict mode for validator when
                        validating mutation data
  -a MAX_REPORTED_VALUES, --max_reported_values MAX_REPORTED_VALUES
                        Cutoff in HTML report for the maximum number of line
                        numbers and values encountered to report for each
                        message. For example, set this to a high number to
                        report all genes that could not be loaded, instead of
                        reporting "GeneA, GeneB, GeneC, 213 more"
```

#### Example
```
python3 validateStudies.py -d path/to/datahub/public -l vsc_cuk_2018 -u https://www.cbioportal.org -html path/to/html_report/
```
