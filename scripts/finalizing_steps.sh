echo "Enter Complete Study Path:"
read study_path

echo "Cleaning up outdated genes..."
cp $DATAHUB_TOOL_HOME/gene-table-update/data-file-migration/gene_info.txt .
cp $DATAHUB_TOOL_HOME/gene-table-update/data-file-migration/outdated_entrez_ids.txt .
cp $DATAHUB_TOOL_HOME/gene-table-update/data-file-migration/outdated_hugo_symbols.txt .
python3 $DATAHUB_TOOL_HOME/gene-table-update/data-file-migration/gene_cleanup_data_file_migration.py -path $study_path -o

echo "Calculating TMB..."
python $DATAHUB_TOOL_HOME/TMB/calculate_tmb/calc_nonsyn_tmb.py -p $DATAHUB_HOME/reference_data/gene_panels -i $study_path
mv $study_path/tmb_output_data_clinical_sample.txt $study_path/data_clinical_sample.txt
