"""Convert data in 
python code to convert
P-0000246-T05	LTB	2
P-0000246-T05	NOTCH4	2
P-0002556-T03	KMT2A	2
P-0003309-T02	ATM	-2

to

Gene	P-0000246-T05	P-0002556-T03	P-0003309-T02
LTB	2	NA	NA
NOTCH4	2	NA	NA
KMT2A	NA	2	NA
ATM	NA	NA	-2

format

Notes: No header need for the input file. Just data rows in sample id, gene, value format

"""

import pandas as pd

# Read data from file
filename = "cna_raw.txt"  # Replace with the actual filename
df = pd.read_csv(filename, delimiter="\t", header=None, names=["Sample", "Gene", "Value"], dtype=str)

# Pivot the DataFrame to convert samples to columns
df_pivot = df.pivot(index="Gene", columns="Sample", values="Value")

# Fill missing values with "NA"
df_pivot = df_pivot.fillna("NA")

# Print the resulting DataFrame
df_pivot.to_csv('data_cna.txt', sep='\t')
