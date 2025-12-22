#!/bin/bash

dirlist=`ls /Users/madupurr/Github/datahub/public`

for dir in $dirlist
do
	python3 gene_cleanup_data_file_migration.py -path /Users/madupurr/Github/datahub/public/$dir -o
done