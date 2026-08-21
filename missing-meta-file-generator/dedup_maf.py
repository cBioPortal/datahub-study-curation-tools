#!/usr/bin/env python3
"""First-wins dedup of MAF records on the cBioPortal validator's duplicate-mutation
key (validateData.py): Entrez_Gene_Id, Chromosome, Start_Position, End_Position,
Variant_Classification, Tumor_Seq_Allele2, HGVSp_Short, Tumor_Sample_Barcode.
In-place rewrite. Usage: dedup_maf.py <maf_file>"""
import sys

KEY_COLUMNS = ["Entrez_Gene_Id", "Chromosome", "Start_Position", "End_Position",
               "Variant_Classification", "Tumor_Seq_Allele2", "HGVSp_Short",
               "Tumor_Sample_Barcode"]

path = sys.argv[1]
tmp_path = path + ".dedup_tmp"
seen = set()
dropped = 0
with open(path) as fin, open(tmp_path, "w") as fout:
    header_cols = None
    key_idx = None
    for line in fin:
        stripped = line.rstrip("\n")
        if header_cols is None:
            fout.write(line)
            if stripped.startswith("#"):
                continue
            header_cols = stripped.split("\t")
            if all(c in header_cols for c in KEY_COLUMNS):
                key_idx = [header_cols.index(c) for c in KEY_COLUMNS]
            continue
        if key_idx is None:
            fout.write(line)
            continue
        parts = stripped.split("\t")
        try:
            key = tuple(parts[i].strip() for i in key_idx)
        except IndexError:
            fout.write(line)
            continue
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        fout.write(line)

import os
os.replace(tmp_path, path)
print(f"{path}: dropped {dropped} duplicate records, {len(seen)} kept")
