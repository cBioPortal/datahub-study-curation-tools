####Step 1 - Clone Github repo (python wrapper)

https://github.com/baudisgroup/segment-liftover

####Step 2 - Download the original executable:

Go to http://hgdownload.cse.ucsc.edu/admin/exe/macOSX.x86_64/
click to download "liftover"

####Step 3 - run the wrapper:
```
sudo python3 segmentLiftover.py -l path/to/liftover/exe -i path/to/input/dir -o path/to/output/dir -c hg18ToHg19 -si input_file_name -so output_file_name --log_path /path/to/log/folder
```

example
```
sudo python3 segmentLiftover.py -l ./liftOver -i ~/data/datahub/public/cellline_nci60/ -o ~/data/datahub/public/cellline_nci60/ -c hg18ToHg19 -si cellline_nci60_data_cna_hg18.seg -so cellline_nci60_data_cna_hg19.seg
```


####Notes:

- python3 need to be installed. Tutorial with homebrew: https://realpython.com/installing-python/#macos-mac-os-x 
- the log folder generated is admin permission only. A bunch of log files were generated, unconverted.log includes the entries that failed in conversion.
