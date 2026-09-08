#!/usr/bin/env python3
"""Fuse extra data_mutations*.txt files into a study's primary data_mutations.txt.

Replicates what the pipelines JAR effectively does (imports all data_mutations*
files into one profile) in a metaImport-compatible way: one MAF, deduplicated on
the validator's duplicate-mutation key.

- Secondary files' records are appended in filename order; columns are remapped
  by header name to the primary's column order (missing columns -> blank,
  surplus secondary columns dropped with a warning).
- After concatenation, first-wins dedup on the validator key (Entrez_Gene_Id,
  Chromosome, Start_Position, End_Position, Variant_Classification,
  Tumor_Seq_Allele2, HGVSp_Short, Tumor_Sample_Barcode).
- Secondary data files and their meta files are deleted.
- '#' comment lines in secondaries are dropped.

Usage: fuse_mafs.py <study_dir> [--exclude data_mutations_uncalled.txt] [--dry-run]
"""
import argparse
import glob
import os

KEY_COLUMNS = ["Entrez_Gene_Id", "Chromosome", "Start_Position", "End_Position",
               "Variant_Classification", "Tumor_Seq_Allele2", "HGVSp_Short",
               "Tumor_Sample_Barcode"]


def read_maf(path):
    comments, header, rows = [], None, []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\r\n")
            if header is None:
                if line.startswith("#"):
                    comments.append(line)
                    continue
                header = line.split("\t")
                continue
            if line.strip():
                rows.append(line.split("\t"))
    return comments, header, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study_dir")
    ap.add_argument("--exclude", action="append", default=[],
                    help="secondary filename to leave alone (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    primary_path = os.path.join(args.study_dir, "data_mutations.txt")
    if not os.path.exists(primary_path):
        raise SystemExit(f"no data_mutations.txt in {args.study_dir}")
    secondaries = sorted(
        p for p in glob.glob(os.path.join(args.study_dir, "data_mutations_*.txt"))
        if os.path.basename(p) not in args.exclude)
    if not secondaries:
        print(f"{args.study_dir}: no secondary MAFs to fuse")
        return

    comments, header, rows = read_maf(primary_path)
    appended = 0
    for sec in secondaries:
        _, sec_header, sec_rows = read_maf(sec)
        col_map = []
        for col in header:
            col_map.append(sec_header.index(col) if col in sec_header else None)
        dropped_cols = [c for c in sec_header if c not in header]
        if dropped_cols:
            print(f"{os.path.basename(sec)}: dropping columns not in primary: {dropped_cols}")
        for r in sec_rows:
            rows.append([("" if i is None or i >= len(r) else r[i]) for i in col_map])
            appended += 1

    key_idx = [header.index(c) for c in KEY_COLUMNS if c in header]
    have_full_key = len(key_idx) == len(KEY_COLUMNS)
    seen = set()
    out_rows = []
    dropped = 0
    for r in rows:
        if have_full_key:
            key = tuple(r[i].strip() if i < len(r) else "" for i in key_idx)
            if key in seen:
                dropped += 1
                continue
            seen.add(key)
        out_rows.append(r)

    print(f"{args.study_dir}: appended {appended} records from "
          f"{[os.path.basename(s) for s in secondaries]}, deduped {dropped}, "
          f"final {len(out_rows)} records" + (" [dry-run]" if args.dry_run else ""))
    if args.dry_run:
        return
    with open(primary_path, "w") as f:
        for c in comments:
            f.write(c + "\n")
        f.write("\t".join(header) + "\n")
        for r in out_rows:
            f.write("\t".join(r) + "\n")
    for sec in secondaries:
        os.remove(sec)
        print(f"removed {os.path.basename(sec)}")
        base = os.path.basename(sec)[len("data_"):]
        for m in glob.glob(os.path.join(args.study_dir, "meta_*")):
            if base in os.path.basename(m):
                os.remove(m)
                print(f"removed {os.path.basename(m)}")


if __name__ == "__main__":
    main()
