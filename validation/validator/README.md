# Introduction

The scripts validate folder(s) of study formatted in cBioPortal format. 
cBioPortal file formats: https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats

# Installation

###Python3
Make sure `python3.x` is installed. Official information at https://www.python.org/downloads/

###yaml
```
python3 -m pip install pyymal
```

###jinja2
```
python3 -m pip install jinja2
```
###set system environment
set env `PYTHONPATH` to path to cbioportal repo scripts folder (`cbioportal/core/src/main/scripts`) on your local machine. 
Use command line every time before running the script (in the same session)
```
export PYTHONPATH=path/to/cbioportal/github/repo/core/src/main/scripts
```

# Usage

```
python3 validateStudies.py -d /Users/suny1/github/datahub/public -l vsc_cuk_2018 -u http://cbioportal.org -html ~/Desktop/
```

```
validateStudies.py [-h] [-d ROOT_DIRECTORY] [-l LIST_OF_STUDIES]
                          [-html HTML_FOLDER]
                          [-u URL_SERVER | -p PORTAL_INFO_DIR | -n]
                          [-P PORTAL_PROPERTIES] [-m] [-a MAX_REPORTED_VALUES]
```
#### Example
```
python3 validateStudies.py -d path/to/datahub/public -l vsc_cuk_2018 -u http://cbioportal.org -html path/to/html_report/
```