import csv
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sample-map", required=True, help="Path to the sample ID map .csv", type=str)
    parser.add_argument("--sample-from", required=True, help='"from ID" field in sample-map file', type=str)
    parser.add_argument("--sample-to", required=True, help='"to ID" field in sample-map file', type=str)

    parser.add_argument("-p", "--patient-map", required=True, help="Path to the patient ID map .csv", type=str)
    parser.add_argument("--patient-from", required=True, help='"from ID" field in patient-map file', type=str)
    parser.add_argument("--patient-to", required=True, help='"to ID" field in patient-map file', type=str)

    parser.add_argument("-path", "--source-path", required=True, help="Path to the study directory", type=str)
    parser.add_argument("-dest", "--dest-path", required=True, help="Path to the destination directory", type=str)

    parser.add_argument("--drop-unknown", help="Not to fail on IDs not found in the map", type=bool, default=False)

    args = parser.parse_args()
    print(args)

    smap = load_map(args.sample_map, args.sample_from, args.sample_to)
    pmap = load_map(args.patient_map, args.patient_from, args.patient_to)

    rewrite_study(args.source_path, args.dest_path, patient_map=pmap, sample_map=smap, strict=not args.drop_unknown)


def load_map(map_fname, from_f, to_f):
    with open(map_fname) as f:
        map_list = list(csv.DictReader(f))

    return {map_dict[from_f]: map_dict[to_f] for map_dict in map_list}


def rewrite_study(study_dir, output_dir, patient_map, sample_map, strict=True):

    for fname in [fname for fname in os.listdir(study_dir) if "data" in fname]:
        header = extract_header(study_dir + "/" + fname)

        by_column = lambda field, map: map_by_ID(study_dir, fname, header.index(field), map, output_dir, strict=strict)

        if "patient_id" in header and "sample_id" not in header:
            by_column("patient_id", patient_map)

        elif "patient_id" in header and "sample_id" in header and "timeline" in fname:
            # map_two(study_dir, fname, header.index("patient_id"), patient_map, header.index("sample_id"), sample_map, output_dir)
            pass  ## TBD

        elif "sample_id" in header:
            by_column("sample_id", sample_map)

        elif "sampleid" in header:
            by_column("sampleid", sample_map)

        elif "tumor_sample_barcode" in header:
            # if "matched_norm_sample_barcode" in header:
            #     # TBD - map two columns.
            #     map_two(study_dir, fname, header.index("tumor_sample_barcode"), sample_map, header.index("matched_norm_sample_barcode"), sample_map, output_dir)

            by_column("tumor_sample_barcode", sample_map)

        elif "id" in header and "chrom" in header:
            raise Exception("Not implemented for id/chrom file type {}".format(fname))
            # by_column("id", sample_map)

        elif ("hugo_symbol" in header or "entrez_gene_id" in header) and "tumor_sample_barcode" not in header:
            index_cols = find_sample_position(fname, header)
            map_matrix_type(study_dir, fname, sample_map, output_dir, index_cols)

        elif "composite.element.ref" in header:
            raise Exception("Not implemented for composite.element.ref file type {}".format(fname))
            # index_cols = find_sample_position(fname, header)
            # map_matrix_type(study_dir, fname, sample_map, output_dir, index_cols)

        elif "entity_stable_id" in header:
            raise Exception("Not implemented for entity_stable_id file type {}".format(fname))
            # index_cols = find_sample_position(fname, header)
            # map_generic_assay(fname, sample_ids_list, output_dir, index_cols)

        else:
            raise Exception("File {} of unknown type".format(fname))

    try:
        os.mkdir(output_dir + "/case_lists")
    except FileExistsError:
        pass

    for cl_fname in os.listdir(study_dir + "/case_lists"):
        map_case_list(study_dir + "/case_lists", cl_fname, sample_map, output_dir + "/case_lists", strict=strict)


def extract_header(filename):
    with open(filename, "r") as infile:
        for line in infile:
            if line.startswith("#"):
                continue
            else:
                return line.lower().rstrip("\n").split("\t")
            break


def map_by_ID(study_dir, fname, index_column, id_map, output_dir, strict=True):

    header_data = ""
    data = ""
    print("Processing file " + fname + " ")

    fullheader = False

    with open(study_dir + "/" + fname, "r") as data_file:
        for lnum, line in enumerate(data_file):

            if line.startswith("#"):  # processing preamble
                header_data += line
            else:
                if fullheader:  # now processing data lines
                    values = line.rstrip("\n").split("\t")

                    current_id = values[index_column]
                    try:
                        new_id = id_map[current_id]
                    except KeyError:
                        if strict:
                            raise Exception("No mapping found for {} used in {}:{}".format(current_id, fname, lnum))
                        else:
                            continue

                    if strict and not new_id:
                        raise Exception("Empty mapping found for {} used in {}:{}".format(current_id, fname, lnum))

                    values[index_column] = new_id
                    data += "\t".join(values) + "\n"

                else:  # first line after preamble is the header
                    header_data += line
                    fullheader = True

    if data != "":
        print("Writing remapped data to " + output_dir + "/" + fname)
        with open(output_dir + "/" + fname, "w") as outfile:
            outfile.write(header_data)
            outfile.write(data)
    else:
        print("Empty remmaped file " + fname + " - skipping..")


# def map_matrix_type(study_dir, file, sample_ids_list, outdir, data_cols):
# def map_matrix_type(study_dir, fname, sample_map, output_dir, data_cols):
#     data = ""
#     data_cols_len = len(data_cols)
#     header_cols = extract_header(study_dir, file)
#     for value in header_cols:
#         if value in sample_map:
#             ind = header_cols.index(value)
#             data_cols.append(ind)
#     if len(data_cols) == data_cols_len:
#         return None

#     print("Processing file " + file + "...")
#     with open(study_dir + "/" + file, "r") as data_file:
#         for line in data_file:
#             if line.startswith("#"):
#                 data += line
#             elif line.startswith(header_cols[0]):
#                 data += "\t".join([header_cols[i] for i in data_cols]) + "\n"
#             else:
#                 line = line.strip("\n").split("\t")
#                 if "" in set([line[i] for i in data_cols]) and len(set([line[i] for i in data_cols])) == 2:
#                     continue
#                 else:
#                     data += "\t".join([line[i] for i in data_cols]) + "\n"

#     if data != "":
#         print("Writing subsetted data to " + outdir + "/" + file + "\n")
#         with open(outdir + "/" + file, "w") as datafile:
#             datafile.write(data.strip("\n"))
#     else:
#         print("Sample IDs to subset are not present in file. Skipping..")


def map_case_list(dir, fname, id_map, output_dir, strict=True):
    data = ""
    with open(dir + "/" + fname) as f:
        for lnum, line in enumerate(f):
            if not line.startswith("case_list_ids: "):
                data += line
            else:
                orig_ids = line.split(" ", 1)[1].split("\t")
                new_ids = []
                for current_id in orig_ids:
                    try:
                        new_ids.append(id_map[current_id])
                    except KeyError:
                        if strict:
                            raise Exception("No mapping found for {} used in {}:{}".format(current_id, fname, lnum))
                        else:
                            continue
                data += "case_list_ids: " + "\t".join(new_ids) + "\n"

    if data != "":
        print("Writing remapped data to " + output_dir + "/" + fname)
        with open(output_dir + "/" + fname, "w") as outfile:
            outfile.write(data)
    else:
        print("Empty remmaped file " + fname + " - skipping..")


def find_sample_position(file, header):
    HEADER_KEYWORDS = [
        "composite.element.ref",
        "hugo_symbol",
        "entrez_gene_id",
        "entity_stable_id",
        "name",
        "description",
        "url",
        "confidence_statement",
    ]
    index_cols = []
    for keyword in header:
        if keyword in HEADER_KEYWORDS:
            index_cols.append(header.index(keyword))
    return index_cols


if __name__ == "__main__":
    main()
