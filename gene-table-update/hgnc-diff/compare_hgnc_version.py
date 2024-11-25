import pandas as pd
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Compare old and new HGNC gene tables.")
parser.add_argument('--old_file', required=True, help='path to the old HGNC file (e.g., hgnc_complete_set_2023-10-01.txt)')
parser.add_argument('--new_file', required=True, help='path to the new HGNC file (e.g., hgnc_complete_set_2024-10-01.txt)')
parser.add_argument('--output_file', required=True, help='Path to the output file (e.g., gene_changes.txt)')
args = parser.parse_args()

# Load the old and new data into pandas dataframes
old_df = pd.read_csv(args.old_file, sep='\t', low_memory=False)
new_df = pd.read_csv(args.new_file, sep='\t', low_memory=False)

# Select relevant columns: Hugo symbol, Entrez ID, and Locus Type
old_df = old_df[['hgnc_id', 'symbol', 'entrez_id', 'locus_type']].copy()
new_df = new_df[['hgnc_id', 'symbol', 'entrez_id', 'locus_type']].copy()

# Convert Entrez IDs to integers where possible and fill missing values with empty strings
old_df['entrez_id'] = old_df['entrez_id'].apply(lambda x: int(x) if pd.notna(x) else "")
new_df['entrez_id'] = new_df['entrez_id'].apply(lambda x: int(x) if pd.notna(x) else "")

# Merge old and new data on 'hgnc_id' to compare the Hugo symbols, Entrez IDs, and Locus Type
merged_df = pd.merge(old_df, new_df, on='hgnc_id', how='outer', suffixes=('_old', '_new'))

# Replace NaNs with empty strings in the merged DataFrame
merged_df.fillna("", inplace=True)

# 1. Genes where both Hugo symbol & Entrez ID have been replaced
both_replaced = merged_df[(merged_df['symbol_old'] != merged_df['symbol_new']) & 
                          (merged_df['entrez_id_old'] != merged_df['entrez_id_new']) &
                          (merged_df['symbol_old'] != "") & (merged_df['entrez_id_old'] != "")]
both_replaced_list = both_replaced[['symbol_old', 'symbol_new', 'entrez_id_old', 'entrez_id_new', 'locus_type_old', 'locus_type_new']]

# 2. Genes where only Entrez ID got updated
entrez_updated = merged_df[(merged_df['entrez_id_old'] != merged_df['entrez_id_new']) & 
                           (merged_df['symbol_old'] == merged_df['symbol_new']) &
                           (merged_df['symbol_old'] != "")]
entrez_updated_list = entrez_updated[['symbol_old', 'entrez_id_old', 'entrez_id_new', 'locus_type_old', 'locus_type_new']]

# 3. Genes where only Hugo symbols got updated
symbol_updated = merged_df[(merged_df['symbol_old'] != merged_df['symbol_new']) & 
                           (merged_df['entrez_id_old'] == merged_df['entrez_id_new']) &
                           (merged_df['entrez_id_old'] != "")]
symbol_updated_list = symbol_updated[['symbol_old', 'symbol_new', 'entrez_id_old', 'locus_type_old', 'locus_type_new']]

# 4. Genes that are not present in the new file but exist in the old file
removed_genes = merged_df[(merged_df['symbol_new'] == "") & (merged_df['symbol_old'] != "")]
removed_genes_list = removed_genes[['symbol_old', 'entrez_id_old', 'locus_type_old']]

# 5. Genes that got added in the new file but do not exist in the old file
added_genes = merged_df[(merged_df['symbol_old'] == "") & (merged_df['symbol_new'] != "")]
added_genes_list = added_genes[['symbol_new', 'entrez_id_new', 'locus_type_new']]

# Write the changes to the specified output file
with open(args.output_file, 'w') as f:
    f.write("1. Genes where both Hugo symbol & Entrez ID have been replaced:\n")
    f.write(both_replaced_list.to_string(index=False))
    f.write("\n\n2. Genes where only Entrez ID got updated:\n")
    f.write(entrez_updated_list.to_string(index=False))
    f.write("\n\n3. Genes where only Hugo symbols got updated:\n")
    f.write(symbol_updated_list.to_string(index=False))
    f.write("\n\n4. Genes that were Removed:\n")
    f.write(removed_genes_list.to_string(index=False))
    f.write("\n\n5. Genes that got Added:\n")
    f.write(added_genes_list.to_string(index=False))

print(f"Gene changes written to '{args.output_file}'.")